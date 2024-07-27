#
/*

	    	C compiler, part 2


*/

#include "c1h.c"

char	maprel[] {	EQUAL, NEQUAL, GREATEQ, GREAT, LESSEQ,
			LESS, GREATQP, GREATP, LESSEQP, LESSP
};

char	notrel[] {	NEQUAL, EQUAL, GREAT, GREATEQ, LESS,
			LESSEQ, GREATP, GREATQP, LESSP, LESSEQP
};

struct tconst czero { CON, INT, 0, 0};
struct tconst cone  { CON, INT, 0, 1};
struct tconst fczero { SFCON, DOUBLE, 0, 0 };

struct	table	*cregtab;

int	nreg	3;
int	isn	10000;
int	namsiz	8;

main(argc, argv)
char *argv[];
{
	extern fout;

	if (argc<4) {
		error("Arg count");
		exit(1);
	}
	if(fopen(argv[1], ascbuf)<0) {
		error("Missing temp file");
		exit(1);
	}
	if ((fout = creat(argv[3], 0666)) < 0) {
		error("Can't create %s", argv[3]);
		exit(1);
	}
	spacep = treespace;
	getree();
	/*
	 * If any floating-point instructions
	 * were used, generate a reference which
	 * pulls in the floating-point part of printf.
	 */
	if (nfloat)
		printf(".globl	fltused\n");
	/*
	 * tack on the string file.
	 */
	close(ascbuf[0]);
	if (fopen(argv[2], ascbuf)<0) {
		error("Missing temp file");
		exit(1);
	}
	printf(".globl\n.data\n");
	getree();
	flush();
	exit(nerror!=0);
}

/*
 * Given a tree, a code table, and a
 * count of available registers, find the code table
 * for the appropriate operator such that the operands
 * are of the right type and the number of registers
 * required is not too large.
 * Return a ptr to the table entry or 0 if none found.
 */
char *match(atree, table, nrleft)
struct tnode *atree;
struct table *table;
{
	int op, d1, d2, t1, t2, dope;
	struct tnode *p2;
	register struct tnode *p1, *tree;
	register struct optab *opt;

	if ((tree=atree)==0)
		return(0);
	if (table==lsptab)
		table = sptab;
	if ((op = tree->op)==0)
		return(0);
	dope = opdope[op];
	if ((dope&LEAF) == 0)
		p1 = tree->tr1;
	else
		p1 = tree;
	t1 = p1->type;
	d1 = dcalc(p1, nrleft);
	if ((dope&BINARY)!=0) {
		p2 = tree->tr2;
		/*
		 * If a subtree starts off with a conversion operator,
		 * try for a match with the conversion eliminated.
		 * E.g. int = double can be done without generating
		 * the converted int in a register by
		 * movf double,fr0; movfi fr0,int .
		 */
		if(opdope[p1->op]&CNVRT && (opdope[p2->op]&CNVRT)==0) {
			tree->tr1 = p1->tr1;
			if (opt = match(tree, table, nrleft))
				return(opt);
			tree->tr1 = p1;
		} else if (opdope[p2->op]&CNVRT && (opdope[p1->op]&CNVRT)==0) {
			tree->tr2 = p2->tr1;
			if (opt = match(tree, table, nrleft))
				return(opt);
			tree->tr2 = p2;
		}
		t2 = p2->type;
		d2 = dcalc(p2, nrleft);
	}
	for (; table->op!=op; table++)
		if (table->op==0)
			return(0);
	for (opt = table->tabp; opt->tabdeg1!=0; opt++) {
		if (d1 > (opt->tabdeg1&077)
		 || (opt->tabdeg1 >= 0100 && (p1->op != STAR)))
			continue;
		if (notcompat(p1, opt->tabtyp1, op)) {
			continue;
		}
		if ((opdope[op]&BINARY)!=0 && p2!=0) {
			if (d2 > (opt->tabdeg2&077)
			 || (opt->tabdeg2 >= 0100) && (p2->op != STAR) )
				continue;
			if (notcompat(p2,opt->tabtyp2, 0))
				continue;
		}
		return(opt);
	}
	return(0);
}

/*
 * Given a tree, a code table, and a register,
 * produce code to evaluate the tree with the appropriate table.
 * Registers reg and upcan be used.
 * If there is a value, it is desired that it appear in reg.
 * The routine returns the register in which the value actually appears.
 * This routine must work or there is an error.
 * If the table called for is cctab, sptab, or efftab,
 * and tree can't be done using the called-for table,
 * another try is made.
 * If the tree can't be compiled using cctab, regtab is
 * used and a "tst" instruction is produced.
 * If the tree can't be compiled using sptab,
 * regtab is used and the register is pushed on the stack.
 * If the tree can't be compiled using efftab,
 * just use regtab.
 * Regtab must succeed or an "op not found" error results.
 *
 * A number of special cases are recognized, and
 * there is an interaction with the optimizer routines.
 */
rcexpr(atree, atable, reg)
struct tnode *atree;
struct table *atable;
{
	register r;
	int modf, nargs, recurf;
	register struct tnode *tree;
	register struct table *table;

	table = atable;
	recurf = 0;
	if (reg<0) {
		recurf++;
		reg = ~reg;
		if (reg>=020) {
			reg =- 020;
			recurf++;
		}
	}
	if((tree=atree)==0)
		return(0);
	switch (tree->op)  {

	/*
	 * A conditional branch
	 */
	case CBRANCH:
		cbranch(optim(tree->btree), tree->lbl, tree->cond, 0);
		return(0);

	/*
	 * An initializing expression
	 */
	case INIT:
		if (tree->tr1->op == AMPER)
			tree->tr1 = tree->tr1->tr1;
		if (tree->tr1->op==NAME)
			pname(tree->tr1);
		else if (tree->tr1==CON)
			psoct(tree->tr1->value);
		else
			error("Illegal initialization");
		putchar('\n');
		return(0);

	/*
	 * Put the value of an expression in r0,
	 * for a switch or a return
	 */
	case RFORCE:
		if((r=rcexpr(tree->tr1, regtab, reg)) != 0)
			printf("mov%c	r%d,r0\n", isfloat(tree->tr1), r);
		return(0);

	/*
	 * sequential execution
	 */
	case COMMA:
		rcexpr(tree->tr1, efftab, reg);
		atree = tree = tree->tr2;
		break;

	/*
	 * In the generated &~ operator,
	 * fiddle things so a PDP-11 "bit"
	 * instruction will be produced when cctab is used.
	 */
	case NAND:
		if (table==cctab) {
			tree->op = TAND;
			tree->tr2 = optim(block(1, COMPL, INT, 0, tree->tr2));
		}
		break;


	/*
	 * Handle a subroutine call. It has to be done
	 * here because if cexpr got called twice, the
	 * arguments might be compiled twice.
	 * There is also some fiddling so the
	 * first argument, in favorable circumstances,
	 * goes to (sp) instead of -(sp), reducing
	 * the amount of stack-popping.
	 */
	case CALL:
		r = 0;
		nargs = 0;
		modf = 0;
		if (tree->tr1->op!=NAME) {	/* get nargs right */
			nargs++;
			nstack++;
		}
		tree = tree->tr2;
		if(tree->op) {
			while (tree->op==COMMA) {
				r =+ comarg(tree->tr2, &modf);
				tree = tree->tr1;
				nargs++;
			}
			r =+ comarg(tree, &modf);
			nargs++;
		}
		tree = atree;
		tree->op = CALL2;
		if (modf && tree->tr1->op==NAME && tree->tr1->class==EXTERN)
			tree->op = CALL1;
		cexpr(tree, regtab, reg);
		popstk(r);
		nstack =- nargs;
		if (table==efftab || table==regtab)
			return(0);
		r = 0;
		goto fixup;

	/*
	 * Longs need special treatment.
	 */
	case ASLSH:
	case LSHIFT:
		if (tree->type==LONG) {
			if (tree->tr2->op==ITOL)
				tree->tr2 = tree->tr2->tr1;
			if (tree->op==ASLSH)
				tree->op = ASLSHL;
			else
				tree->op = LLSHIFT;
		}
		break;

	/*
	 * Try to change * and / to shifts.
	 */
	case TIMES:
	case DIVIDE:
	case ASTIMES:
	case ASDIV:
		tree = pow2(tree);
	}
	/*
	 * Try to find postfix ++ and -- operators that can be
	 * pulled out and done after the rest of the expression
	 */
	if (table!=cctab && table!=cregtab && recurf<2
	 && (opdope[tree->op]&LEAF)==0) {
		if (r=delay(&atree, table, reg)) {
			tree = atree;
			table = efftab;
			reg = r-1;
		}
	}
	/*
	 * Basically, try to reorder the computation
	 * so  reg = x+y  is done as  reg = x; reg =+ y
	 */
	if (recurf==0 && reorder(&atree, table, reg)) {
		if (table==cctab && atree->op==NAME)
			return(reg);
	}
	tree = atree;
	if (table==efftab && tree->op==NAME)
		return(reg);
	if ((r=cexpr(tree, table, reg))>=0)
		return(r);
	if (table!=regtab)  {
		if((r=cexpr(tree, regtab, reg))>=0) {
	fixup:
			modf = isfloat(tree);
			if (table==sptab || table==lsptab) {
				if (tree->type==LONG) {
					printf("mov\tr%d,-(sp)\n",r+1);
					nstack++;
				}
				printf("mov%c	r%d,%c(sp)\n", modf, r,
					table==sptab? '-':0);
				nstack++;
			}
			if (table==cctab)
				printf("tst%c	r%d\n", modf, r);
			return(r);
		}
	}
	if (tree->op>0 && tree->op<RFORCE && opntab[tree->op])
		error("No code table for op: %s", opntab[tree->op]);
	else
		error("No code table for op %d", tree->op);
	return(reg);
}

/*
 * Try to compile the tree with the code table using
 * registers areg and up.  If successful,
 * return the register where the value actually ended up.
 * If unsuccessful, return -1.
 *
 * Most of the work is the macro-expansion of the
 * code table.
 */
cexpr(atree, table, areg)
struct tnode *atree;
struct table *table;
{
	int c, r;
	register struct tnode *p, *p1, *tree;
	struct table *ctable;
	struct tnode *p2;
	char *string;
	int reg, reg1, rreg, flag, opd;
	char *opt;

	tree = atree;
	reg = areg;
	p1 = tree->tr2;
	c = tree->op;
	opd = opdope[c];
	/*
	 * When the value of a relational or a logical expression is
	 * desired, more work must be done.
	 */
	if ((opd&RELAT||c==LOGAND||c==LOGOR||c==EXCLA) && table!=cctab) {
		cbranch(tree, c=isn++, 1, reg);
		rcexpr(&czero, table, reg);
		branch(isn, 0);
		label(c);
		rcexpr(&cone, table, reg);
		label(isn++);
		return(reg);
	}
	if(c==QUEST) {
		if (table==cctab)
			return(-1);
		cbranch(tree->tr1, c=isn++, 0, reg);
		flag = nstack;
		rreg = rcexpr(p1->tr1, table, reg);
		nstack = flag;
		branch(r=isn++, 0);
		label(c);
		reg = rcexpr(p1->tr2, table, rreg);
		if (rreg!=reg)
			printf("mov%c	r%d,r%d\n",
			    isfloat(tree),reg,rreg);
		label(r);
		return(rreg);
	}
	reg = oddreg(tree, reg);
	reg1 = reg+1;
	/*
	 * long values take 2 registers.
	 */
	if (tree->type==LONG && tree->op!=ITOL)
		reg1++;
	/*
	 * Leaves of the expression tree
	 */
	if ((r = chkleaf(tree, table, reg)) >= 0)
		return(r);
	/*
	 * x + (-1) is better done as x-1.
	 */

	if ((tree->op==PLUS||tree->op==ASPLUS) &&
	    (p1=tree->tr2)->op == CON && p1->value == -1) {
		p1->value = 1;
		tree->op =+ (MINUS-PLUS);
	}
	if (table==cregtab)
		table = regtab;
	/*
	 * The following peculiar code depends on the fact that
	 * if you just want the codition codes set, efftab
	 * will generate the right code unless the operator is
	 * postfix ++ or --. Unravelled, if the table is
	 * cctab and the operator is not special, try first
	 * for efftab;  if the table isn't, if the operator is,
	 * or the first match fails, try to match
	 * with the table actually asked for.
	 */
	if (table!=cctab || c==INCAFT || c==DECAFT
	 || (opt = match(tree, efftab, nreg-reg)) == 0)
		if ((opt=match(tree, table, nreg-reg))==0)
			return(-1);
	string = opt->tabstring;
	p1 = tree->tr1;
	p2 = 0;
	if (opdope[tree->op]&BINARY)
		p2 = tree->tr2;
loop:
	/*
	 * The 0200 bit asks for a tab.
	 */
	if ((c = *string++) & 0200) {
		c =& 0177;
		putchar('\t');
	}
	switch (c) {

	case '\0':
		if (!isfloat(tree))
			if (tree->op==DIVIDE || tree->op==ASDIV)
				reg--;
		return(reg);

	/* A1 */
	case 'A':
		p = p1;
		goto adr;

	/* A2 */
	case 'B':
		p = p2;
		goto adr;

	adr:
		c = 0;
		if (*string=='\'') {
			c = 1;
			string++;
		} else if (*string=='+') {
			c = 2;
			string++;
		}
		pname(p, c);
		goto loop;

	/* I */
	case 'M':
		if ((c = *string)=='\'')
			string++;
		else
			c = 0;
		prins(tree->op, c, instab);
		goto loop;

	/* B1 */
	case 'C':
		if ((opd&LEAF) != 0)
			p = tree;
		else
			p = p1;
		goto pbyte;

	/* BF */
	case 'P':
		p = tree;
		goto pb1;

	/* B2 */
	case 'D':
		p = p2;
	pbyte:
		if (p->type==CHAR)
			putchar('b');
	pb1:
		if (isfloat(p))
			putchar('f');
		goto loop;

	/* BE */
	case 'L':
		if (p1->type==CHAR || p2->type==CHAR)
			putchar('b');
		p = tree;
		goto pb1;

	/* F */
	case 'G':
		p = p1;
		flag = 01;
		goto subtre;

	/* S */
	case 'K':
		p = p2;
		flag = 02;
		goto subtre;

	/* H */
	case 'H':
		p = tree;
		flag = 04;

	subtre:
		ctable = regtab;
		c = *string++ - 'A';
		if (*string=='!') {
			string++;
			c =| 020;	/* force right register */
		}
		if ((c&02)!=0)
			ctable = sptab;
		if ((c&04)!=0)
			ctable = cctab;
		if ((flag&01) && ctable==regtab && (c&01)==0
		  && (tree->op==DIVIDE||tree->op==MOD
		   || tree->op==ASDIV||tree->op==ASMOD))
			ctable = cregtab;
		if ((c&01)!=0) {
			p = p->tr1;
			if(collcon(p) && ctable!=sptab) {
				if (p->op==STAR)
					p = p->tr1;
				p = p->tr1;
			}
		}
		if (table==lsptab && ctable==sptab)
			ctable = lsptab;
		if (c&010)
			r = reg1;
		else
			if (opdope[p->op]&LEAF || p->degree < 2)
				r = reg;
			else
				r = areg;
		rreg = rcexpr(p, ctable, r);
		if (ctable!=regtab && ctable!=cregtab)
			goto loop;
		if (c&010) {
			if (c&020 && rreg!=reg1)
				printf("mov%c	r%d,r%d\n",
				    isfloat(tree),rreg,reg1);
			else
				reg1 = rreg;
		} else if (rreg!=reg)
			if ((c&020)==0 && oddreg(tree, 0)==0 && (flag&04 ||
			      flag&01
			  && xdcalc(p2, nreg-rreg-1) <= (opt->tabdeg2&077)
			 ||   flag&02
			  && xdcalc(p1,nreg-rreg-1) <= (opt->tabdeg1&077))) {
				reg = rreg;
				reg1 = rreg+1;
			} else
				printf("mov%c\tr%d,r%d\n",
				    isfloat(tree), rreg, reg);
		goto loop;

	/* R */
	case 'I':
		r = reg;
		if (*string=='-') {
			string++;
			r--;
		}
		goto preg;

	/* R1 */
	case 'J':
		r = reg1;
	preg:
		if (*string=='+') {
			string++;
			r++;
		}
		if (r>nreg)
			error("Register overflow: simplify expression");
		printf("r%d", r);
		goto loop;

	case '-':		/* check -(sp) */
		if (*string=='(') {
			nstack++;
			if (table!=lsptab)
				putchar('-');
			goto loop;
		}
		break;

	case ')':		/* check (sp)+ */
		putchar(')');
		if (*string=='+')
			nstack--;
		goto loop;

	/* #1 */
	case '#':
		p = p1->tr1;
		goto nmbr;

	/* #2 */
	case '"':
		p = p2->tr1;

	nmbr:
		if(collcon(p)) {
			if (p->op==STAR) {
				printf("*");
				p = p->tr1;
			}
			if ((p = p->tr2)->op == CON) {
				if (p->value)
					psoct(p->value);
			} else if (p->op==AMPER)
				pname(p->tr1, 0);
		}
		goto loop;

	case 'T':		/* "tst R" if 1st op not in cctab */
		if (dcalc(p1, 5)>12 && !match(p1, cctab, 10))
			printf("tst	r%d\n", reg);
		goto loop;
	case 'V':	/* adc or sbc as required for longs */
		switch(tree->op) {
		case PLUS:
		case ASPLUS:
		case INCBEF:
		case INCAFT:
			printf("adc");
			break;

		case MINUS:
		case ASMINUS:
		case NEG:
		case DECBEF:
		case DECAFT:
			printf("sbc");
			break;

		default:
			while ((c = *string++)!='\n' && c!='\0');
			break;
		}
		goto loop;
	}
	putchar(c);
	goto loop;
}

/*
 * This routine just calls sreorder (below)
 * on the subtrees and then on the tree itself.
 * It returns non-zero if anything changed.
 */
reorder(treep, table, reg)
struct tnode **treep;
struct table *table;
{
	register r, r1;
	register struct tnode *p;

	p = *treep;
	if (opdope[p->op]&LEAF)
		return(0);
	r1 = 0;
	while(sreorder(&p->tr1, table, reg))
		r1++;
	if (opdope[p->op]&BINARY) 
		while(sreorder(&p->tr2, table, reg))
			r1++;
	r = 0;
	while (sreorder(treep, table, reg))
		r++;
	*treep = optim(*treep);
	return(r);
}

/*
 * Basically this routine carries out two kinds of optimization.
 * First, it observes that "x + (reg = y)" where actually
 * the = is any assignment op is better done as "reg=y; x+reg".
 * In this case rcexpr is called to do the first part and the
 * tree is modified so the name of the register
 * replaces the assignment.
 * Moreover, expressions like "reg = x+y" are best done as
 * "reg = x; reg =+ y" (so long as "reg" and "y" are not the same!).
 */
sreorder(treep, table, reg)
struct tnode **treep;
struct table *table;
{
	register struct tnode *p, *p1;

	p = *treep;
	if (opdope[p->op]&LEAF)
		return(0);
	if (p->op==PLUS)
		if (reorder(&p->tr2, table, reg))
			*treep = p = optim(p);
	p1 = p->tr1;
	if (p->op==STAR || p->op==PLUS) {
		if (reorder(&p->tr1, table, reg))
			*treep = p = optim(p);
		p1 = p->tr1;
	}
	if (p1->op==NAME) switch(p->op) {
		case ASLSH:
		case ASRSH:
		case ASSIGN:
			if (p1->class != REG || isfloat(p->tr2))
				return(0);
			if (p->op==ASSIGN) switch (p->tr2->op) {
			case TIMES:
			case DIVIDE:
				if (!ispow2(p->tr2))
					break;
				p->tr2 = pow2(p->tr2);
			case PLUS:
			case MINUS:
			case AND:
			case NAND:
			case OR:
			case EXOR:
			case LSHIFT:
			case RSHIFT:
				p1 = p->tr2->tr2;
				if (xdcalc(p1) > 12
				 || p1->op==NAME
				 &&(p1->nloc==p->tr1->nloc
				  || p1->regno==p->tr1->nloc))
					return(0);
				p1 = p->tr2;
				p->tr2 = p1->tr1;
				if (p1->tr1->op!=NAME
				 || p1->tr1->class!=REG
				 || p1->tr1->nloc!=p->tr1->nloc)
					rcexpr(p, efftab, reg);
				p->tr2 = p1->tr2;
				p->op = p1->op + ASPLUS - PLUS;
				*treep = p;
				return(1);
			}
			goto OK;

		case ASTIMES:
		case ASDIV:
			if (!ispow2(p))
				return(0);
		case ASPLUS:
		case ASMINUS:
		case ASSAND:
		case ASSNAND:
		case ASOR:
		case ASXOR:
		case DECBEF:
		case INCBEF:
		OK:
			if (table==cctab||table==cregtab)
				reg =+ 020;
			rcexpr(optim(p), efftab, ~reg);
			*treep = p1;
			return(1);
	}
	return(0);
}

/*
 * Delay handles postfix ++ and -- 
 * It observes that "x + y++" is better
 * treated as "x + y; y++".
 * If the operator is ++ or -- itself,
 * it calls rcexpr to load the operand, letting
 * the calling instance of rcexpr to do the
 * ++ using efftab.
 * Otherwise it uses sdelay to search for inc/dec
 * among the operands.
 */
delay(treep, table, reg)
struct tnode **treep;
{
	register struct tnode *p, *p1;
	register r;

	p = *treep;
	if (table!=efftab && (p->op==INCAFT||p->op==DECAFT)
	 && p->tr1->op==NAME) {
		return(1+rcexpr(p->tr1, table, reg));
	}
	p1 = 0;
	if (opdope[p->op]&BINARY)
		p1 = sdelay(&p->tr2);
	if (p1==0)
		p1 = sdelay(&p->tr1);
	if (p1) {
		r = rcexpr(optim(p), table, reg);
		*treep = p1;
		return(r+1);
	}
	return(0);
}

sdelay(ap)
struct tnode **ap;
{
	register struct tnode *p, *p1;

	p = *ap;
	if ((p->op==INCAFT||p->op==DECAFT) && p->tr1->op==NAME) {
		*ap = ncopy(p->tr1);
		return(p);
	}
	if (p->op==STAR || p->op==PLUS)
		if (p1=sdelay(&p->tr1))
			return(p1);
	if (p->op==PLUS)
		return(sdelay(&p->tr2));
	return(0);
}

/*
 * Copy a tree node for a register variable.
 * Used by sdelay because if *reg-- is turned
 * into *reg; reg-- the *reg will in turn
 * be changed to some offset class, accidentally
 * modifying the reg--.
 */
ncopy(ap)
struct tname *ap;
{
	register struct tname *p;

	p = ap;
	if (p->class!=REG)
		return(p);
	return(block(3, NAME, p->type, p->elsize, p->tr1,
	    p->offset, p->nloc));
}

/*
 * If the tree can be immediately loaded into a register,
 * produce code to do so and return success.
 */
chkleaf(atree, table, reg)
struct tnode *atree;
{
	struct tnode lbuf;
	register struct tnode *tree;

	tree = atree;
	if (tree->op!=STAR && dcalc(tree, nreg-reg) > 12)
		return(-1);
	lbuf.op = LOAD;
	lbuf.type = tree->type;
	lbuf.degree = tree->degree;
	lbuf.tr1 = tree;
	return(rcexpr(&lbuf, table, reg));
}

/*
 * Compile a function argument.
 * If the stack is currently empty, put it in (sp)
 * rather than -(sp); this will save a pop.
 * Return the number of bytes pushed,
 * for future popping.
 */
comarg(atree, flagp)
int *flagp;
{
	register struct tnode *tree;
	register retval;

	tree = atree;
	if (nstack || isfloat(tree) || tree->type==LONG) {
		rcexpr(tree, sptab, 0);
		retval = arlength(tree->type);
	} else {
		(*flagp)++;
		rcexpr(tree, lsptab, 0);
		retval = 0;
	}
	return(retval);
}
#
/*
 *  C compiler
 */

#include "c1h.c"

max(a, b)
{
	if (a>b)
		return(a);
	return(b);
}

degree(at)
struct tnode *at;
{
	register struct tnode *t, *t1;

	if ((t=at)==0 || t->op==0)
		return(0);
	if (t->op == CON)
		return(-3);
	if (t->op == AMPER)
		return(-2);
	if (t->op==ITOL && (t1 = isconstant(t)) && t1->value>= 0)
		return(-2);
	if ((opdope[t->op] & LEAF) != 0) {
		if (t->type==CHAR || t->type==FLOAT)
			return(1);
		return(0);
	}
	return(t->degree);
}

pname(ap, flag)
struct tnode *ap;
{
	register i;
	register struct tnode *p;

	p = ap;
loop:
	switch(p->op) {

	case SFCON:
	case CON:
		printf("$");
		psoct(p->value);
		return;

	case FCON:
		printf("L%d", p->value);
		return;

	case NAME:
		i = p->offset;
		if (flag==2)
			i =+ 2;
		if (i) {
			psoct(i);
			if (p->class!=OFFS)
				putchar('+');
			if (p->class==REG)
				regerr();
		}
		switch(p->class) {

		case SOFFS:
		case XOFFS:
			pbase(p);

		case OFFS:
			printf("(r%d)", p->regno);
			return;

		case EXTERN:
		case STATIC:
			pbase(p);
			return;

		case REG:
			printf("r%d", p->nloc);
			return;

		}
		error("Compiler error: pname");
		return;

	case AMPER:
		putchar('$');
		p = p->tr1;
		if (p->op==NAME && p->class==REG)
			regerr();
		goto loop;

	case AUTOI:
		printf("(r%d)%c", p->nloc, flag==1?0:'+');
		return;

	case AUTOD:
		printf("%c(r%d)", flag==1?0:'-', p->nloc);
		return;

	case STAR:
		p = p->tr1;
		putchar('*');
		goto loop;

	}
	error("pname called illegally");
}

regerr()
{
	error("Illegal use of register");
}

pbase(ap)
struct tnode *ap;
{
	register struct tnode *p;

	p = ap;
	if (p->class==SOFFS || p->class==STATIC)
		printf("L%d", p->nloc);
	else
		printf("_%.8s", &(p->nloc));
}

xdcalc(ap, nrleft)
struct tnode *ap;
{
	register struct tnode *p;
	register d;

	p = ap;
	d = dcalc(p, nrleft);
	if (d<20 && p->type==CHAR) {
		if (nrleft>=1)
			d = 20;
		else
			d = 24;
	}
	return(d);
}

dcalc(ap, nrleft)
struct tnode *ap;
{
	register struct tnode *p, *p1;

	if ((p=ap)==0)
		return(0);
	switch (p->op) {

	case NAME:
		if (p->class==REG)
			return(9);

	case AMPER:
	case FCON:
	case AUTOI:
	case AUTOD:
		return(12);

	case CON:
	case SFCON:
		if (p->value==0)
			return(4);
		if (p->value==1)
			return(5);
		if (p->value > 0)
			return(8);
		return(12);

	case STAR:
		p1 = p->tr1;
		if (p1->op==NAME||p1->op==CON||p1->op==AUTOI||p1->op==AUTOD)
			if (p->type!=LONG)
				return(12);
	}
	if (p->type==LONG)
		nrleft--;
	return(p->degree <= nrleft? 20: 24);
}

notcompat(ap, ast, op)
struct tnode *ap;
{
	register at, st;
	register struct tnode *p;

	p = ap;
	at = p->type;
	st = ast;
	if (st==0)		/* word, byte */
		return(at>CHAR && at<PTR);
	if (st==1)		/* word */
		return(at>INT && at<PTR);
	st =- 2;
	if ((at&(~(TYPE+XTYPE))) != 0)
		at = 020;
	if ((at&(~TYPE)) != 0)
		at = at&TYPE | 020;
	if (st==FLOAT && at==DOUBLE)
		at = FLOAT;
	if (p->op==NAME && p->class==REG && op==ASSIGN && st==CHAR)
		return(0);
	return(st != at);
}

prins(op, c, itable)
struct instab *itable;
{
	register struct instab *insp;
	register char *ip;

	for (insp=itable; insp->op != 0; insp++) {
		if (insp->op == op) {
			ip = c? insp->str2: insp->str1;
			if (ip==0)
				break;
			printf("%s", ip);
			return;
		}
	}
	error("No match' for op %d", op);
}

collcon(ap)
struct tnode *ap;
{
	register op;
	register struct tnode *p;

	p = ap;
	if (p->op==STAR)
		p = p->tr1;
	if (p->op==PLUS) {
		op = p->tr2->op;
		if (op==CON || op==AMPER)
			return(1);
	}
	return(0);
}

isfloat(at)
struct tnode *at;
{
	register struct tnode *t;

	t = at;
	if ((opdope[t->op]&RELAT)!=0)
		t = t->tr1;
	if (t->type==FLOAT || t->type==DOUBLE) {
		nfloat = 1;
		return('f');
	}
	return(0);
}

oddreg(t, areg)
struct tnode *t;
{
	register reg;

	reg = areg;
	if (!isfloat(t))
		switch(t->op) {
		case DIVIDE:
		case MOD:
		case ASDIV:
		case ASMOD:
			reg++;

		case TIMES:
		case ASTIMES:
			return(reg|1);
		}
	return(reg);
}

arlength(t)
{
	if (t>=PTR)
		return(2);
	switch(t) {

	case INT:
	case CHAR:
		return(2);

	case LONG:
		return(4);

	case FLOAT:
	case DOUBLE:
		return(8);
	}
	return(1024);
}

/*
 * Strings for switch code.
 */

char	dirsw[] {"\
cmp	r0,$%o\n\
jhi	L%d\n\
asl	r0\n\
jmp	*L%d(r0)\n\
.data\n\
L%d:\
" };

char	simpsw[] {"\
mov	$L%d,r1\n\
mov	r0,L%d\n\
L%d:cmp	r0,(r1)+\n\
jne	L%d\n\
jmp	*L%d-L%d(r1)\n\
.data\n\
L%d:\
"};

char	hashsw[] {"\
mov	r0,r1\n\
clr	r0\n\
div	$%o,r0\n\
asl	r1\n\
add	$L%d,r1\n\
mov	r0,*(r1)+\n\
mov	(r1)+,r1\n\
L%d:cmp	r0,-(r1)\n\
jne	L%d\n\
jmp	*L%d-L%d(r1)\n\
.data\n\
L%d:\
"};

pswitch(afp, alp, deflab)
struct swtab *afp, *alp;
{
	int tlab, ncase, i, j, tabs, worst, best, range;
	register struct swtab *swp, *fp, *lp;
	int poctab[swsiz];

	fp = afp;
	lp = alp;
	if (fp==lp) {
		printf("jbr	L%d\n", deflab);
		return;
	}
	tlab = isn++;
	if (sort(fp, lp))
		return;
	ncase = lp-fp;
	lp--;
	range = lp->swval - fp->swval;
	/* direct switch */
	if (range>0 && range <= 3*ncase) {
		if (fp->swval)
			printf("sub	$%o,r0\n", fp->swval);
		printf(dirsw, range, deflab, isn, isn);
		isn++;
		for (i=fp->swval; i<=lp->swval; i++) {
			if (i==fp->swval) {
				printf("L%d\n", fp->swlab);
				fp++;
			} else
				printf("L%d\n", deflab);
		}
		goto esw;
	}
	/* simple switch */
	if (ncase<8) {
		i = isn++;
		j = isn++;
		printf(simpsw, i, j, isn, isn, j, i, i);
		isn++;
		for (; fp<=lp; fp++)
			printf("%o\n", fp->swval);
		printf("L%d:..\n", j);
		for (fp = afp; fp<=lp; fp++)
			printf("L%d\n", fp->swlab);
		printf("L%d\n", deflab);
		goto esw;
	}
	/* hash switch */
	best = 077777;
	for (i=ncase/4; i<=ncase/2; i++) {
		for (j=0; j<i; j++)
			poctab[j] = 0;
		for (swp=fp; swp<=lp; swp++)
			poctab[lrem(0, swp->swval, i)]++;
		worst = 0;
		for (j=0; j<i; j++)
			if (poctab[j]>worst)
				worst = poctab[j];
		if (i*worst < best) {
			tabs = i;
			best = i*worst;
		}
	}
	i = isn++;
	printf(hashsw, tabs, isn, i, i, isn+tabs+1, isn+1, isn);
	isn++;
	for (i=0; i<=tabs; i++)
		printf("L%d\n", isn+i);
	for (i=0; i<tabs; i++) {
		printf("L%d:..\n", isn++);
		for (swp=fp; swp<=lp; swp++)
			if (lrem(0, swp->swval, tabs) == i)
				printf("%o\n", ldiv(0, swp->swval, tabs));
	}
	printf("L%d:", isn++);
	for (i=0; i<tabs; i++) {
		printf("L%d\n", deflab);
		for (swp=fp; swp<=lp; swp++)
			if (lrem(0, swp->swval, tabs) == i)
				printf("L%d\n", swp->swlab);
	}
esw:
	printf(".text\n");
}

sort(afp, alp)
struct swtab *afp, *alp;
{
	register struct swtab *cp, *fp, *lp;
	int intch, t;

	fp = afp;
	lp = alp;
	while (fp < --lp) {
		intch = 0;
		for (cp=fp; cp<lp; cp++) {
			if (cp->swval == cp[1].swval) {
				error("Duplicate case (%d)", cp->swval);
				return(1);
			}
			if (cp->swval > cp[1].swval) {
				intch++;
				t = cp->swval;
				cp->swval = cp[1].swval;
				cp[1].swval = t;
				t = cp->swlab;
				cp->swlab = cp[1].swlab;
				cp[1].swlab = t;
			}
		}
		if (intch==0)
			break;
	}
	return(0);
}

ispow2(atree)
{
	register int d;
	register struct tnode *tree;

	tree = atree;
	if (!isfloat(tree) && tree->tr2->op==CON) {
		d = tree->tr2->value;
		if (d>1 && (d&(d-1))==0)
			return(d);
	}
	return(0);
}

pow2(atree)
struct tnode *atree;
{
	register int d, i;
	register struct tnode *tree;

	tree = atree;
	if (d = ispow2(tree)) {
		for (i=0; (d=>>1)!=0; i++);
		tree->tr2->value = i;
		d = tree->op;
		tree->op = d==TIMES? LSHIFT:
			  (d==DIVIDE? RSHIFT:
			  (d==ASTIMES? ASLSH: ASRSH));
		tree = optim(tree);
	}
	return(tree);
}

cbranch(atree, albl, cond, areg)
struct tnode *atree;
{
	int l1, op;
	register lbl, reg;
	register struct tnode *tree;

	lbl = albl;
	reg = areg;
	if ((tree=atree)==0)
		return;
	switch(tree->op) {

	case LOGAND:
		if (cond) {
			cbranch(tree->tr1, l1=isn++, 0, reg);
			cbranch(tree->tr2, lbl, 1, reg);
			label(l1);
		} else {
			cbranch(tree->tr1, lbl, 0, reg);
			cbranch(tree->tr2, lbl, 0, reg);
		}
		return;

	case LOGOR:
		if (cond) {
			cbranch(tree->tr1, lbl, 1, reg);
			cbranch(tree->tr2, lbl, 1, reg);
		} else {
			cbranch(tree->tr1, l1=isn++, 1, reg);
			cbranch(tree->tr2, lbl, 0, reg);
			label(l1);
		}
		return;

	case EXCLA:
		cbranch(tree->tr1, lbl, !cond, reg);
		return;

	case COMMA:
		rcexpr(tree->tr1, efftab, reg);
		tree = tree->tr2;
		break;
	}
	op = tree->op;
	if (tree->type==LONG || opdope[op]&RELAT&&tree->tr1->type==LONG) {
		if (tree->type!=LONG) {
			tree->op = MINUS;
			tree->type = LONG;
			tree = optim(tree);
		} else
			op = NEQUAL;
		rcexpr(tree, regtab, 0);
		printf("ashc	$0,r0\n");
		branch(lbl, op, !cond);
		return;
	}
	rcexpr(tree, cctab, reg);
	op = tree->op;
	if ((opdope[op]&RELAT)==0)
		op = NEQUAL;
	else {
		l1 = tree->tr2->op;
	 	if ((l1==CON || l1==SFCON) && tree->tr2->value==0)
			op =+ 200;		/* special for ptr tests */
		else
			op = maprel[op-EQUAL];
	}
	if (isfloat(tree))
		printf("cfcc\n");
	branch(lbl, op, !cond);
}

branch(lbl, aop, c)
{
	register op;

	if(op=aop)
		prins(op, c, branchtab);
	else
		printf("jbr");
	printf("\tL%d\n", lbl);
}

label(l)
{
	printf("L%d:", l);
}

popstk(a)
{
	switch(a) {

	case 0:
		return;

	case 2:
		printf("tst	(sp)+\n");
		return;

	case 4:
		printf("cmp	(sp)+,(sp)+\n");
		return;
	}
	printf("add	$%o,sp\n", a);
}

error(s, p1, p2, p3, p4, p5, p6)
{
	register f;
	extern fout;

	nerror++;
	flush();
	f = fout;
	fout = 1;
	printf("%d: ", line);
	printf(s, p1, p2, p3, p4, p5, p6);
	putchar('\n');
	flush();
	fout = f;
}

psoct(an)
{
	register int n, sign;

	sign = 0;
	if ((n = an) < 0) {
		n = -n;
		sign = '-';
	}
	printf("%c%o", sign, n);
}

/*
 * Read in an intermediate file.
 */
getree()
{
	struct tnode *expstack[20];
	register struct tnode **sp;
	register t, op;
	static char s[9];
	struct swtab *swp;

	spacep = treespace;
	sp = expstack;
	for (;;) {
		if (sp >= &expstack[20])
			error("Stack botch");
		op = getw(ascbuf);
		if ((op&0177400) != 0177000) {
			error("Intermediate file error");
			exit(1);
		}
		switch(op =& 0377) {

	case EOF:
		return;

	case BDATA:
		printf(".byte ");
		seq(',');
		break;

	case WDATA:
		seq(';');
		break;

	case PROG:
		printf(".text\n");
		break;

	case DATA:
		printf(".data\n");
		break;

	case BSS:
		printf(".bss\n");
		break;

	case SYMDEF:
		printf(".globl	_%s\n", outname(s));
		break;

	case RETRN:
		printf("jmp	cret\n");
		break;

	case CSPACE:
		t = outname(s);
		printf(".comm	_%s,%o\n", t, getw(ascbuf));
		break;

	case SSPACE:
		printf(".=.+%o\n", getw(ascbuf));
		break;

	case EVEN:
		printf(".even\n");
		break;

	case SAVE:
		printf("jsr	r5,csv\n");
		t = getw(ascbuf)-6;
		if (t==2)
			printf("tst	-(sp)\n");
		else if (t > 2)
			printf("sub	$%o,sp\n", t);
		break;

	case PROFIL:
		t = getw(ascbuf);
		printf("mov	$L%d,r0\njsr	pc,mcount\n", t);
		printf(".bss\nL%d:.=.+2\n.text\n", t);
		break;

	case SNAME:
		t = outname(s);
		printf("~%s=L%d\n", t, getw(ascbuf));
		break;

	case ANAME:
		t = outname(s);
		printf("~%s=%o\n", t, getw(ascbuf));
		break;

	case RNAME:
		t = outname(s);
		printf("~%s=r%d\n", t, getw(ascbuf));
		break;

	case SWIT:
		t = getw(ascbuf);
		line = getw(ascbuf);
		swp = treespace;
		while (swp->swlab = getw(ascbuf)) {
			swp->swval = getw(ascbuf);
			swp++;
		}
		pswitch(treespace, swp, t);
		break;

	case EXPR:
		line = getw(ascbuf);
		if (sp != &expstack[1]) {
			error("Expression input botch\n");
			exit(1);
		}
		nstack = 0;
		rcexpr(optim(*--sp), efftab, 0);
		spacep = treespace;
		break;

	case NAME:
		t = getw(ascbuf);
		if (t==EXTERN) {
			t = getw(ascbuf);
			*sp = block(6, NAME, t, 0, EXTERN, 0, 0,0,0,0);
			outname(&(*sp)->nloc);
			sp++;
			break;
		}
		*sp = block(3, NAME, 0, 0, t, 0, 0);
		(*sp)->type = getw(ascbuf);
		(*sp)->nloc = getw(ascbuf);
		sp++;
		break;

	case CON:
	case SFCON:
	case FCON:
		t = getw(ascbuf);
		*sp++ = block(1, op, t, 0, getw(ascbuf));
		break;

	case FSEL:
		t = getw(ascbuf);
		sp[-1] = block(2, op, t, 0, sp[-1], getw(ascbuf));
		break;

	case NULL:
		*sp++ = block(0, 0, 0, 0);
		break;

	case CBRANCH:
		t = getw(ascbuf);
		sp[-1] = block(1, CBRANCH, sp[-1], t, getw(ascbuf));
		break;

	case LABEL:
		label(getw(ascbuf));
		break;

	case NLABEL:
		printf("_%s:\n", outname(s));
		break;

	case RLABEL:
		t = outname(s);
		printf("_%s:\n~~%s:\n", t, t);
		break;

	case BRANCH:
		branch(getw(ascbuf), 0);
		break;

	case SETREG:
		nreg = getw(ascbuf)-1;
		break;

	default:
		if (opdope[op]&BINARY) {
			if (sp < &expstack[1]) {
				error("Binary expression botch");
				exit(1);
			}
			t = *--sp;
			*sp++ = block(2, op, getw(ascbuf), 0, *--sp, t);
		} else {
			sp[-1] = block(1, op, getw(ascbuf), 0, sp[-1]);
		}
		break;
	}
	}
}

outname(s)
{
	register char *p, c;
	register n;

	p = s;
	n = 0;
	while (c = getc(ascbuf)) {
		*p++ = c;
		n++;
	}
	while (n++ < 8)
		*p++ = 0;
	return(s);
}

seq(c)
{
	register o;

	if (getw(ascbuf) == 0)
		return;
	for (;;) {
		printf("%o", getw(ascbuf));
		if ((o = getw(ascbuf)) != 1)
			break;
		printf("%c", c);
	}
	printf("\n");
}
#
/*
 *		C compiler part 2 -- expression optimizer
 *
 */

#include "c1h.c"

optim(atree)
struct tnode *atree;
{
	register op, dope;
	int d1, d2;
	struct tnode *t;
	register struct tnode *tree;

	if ((tree=atree)==0)
		return(0);
	if ((op = tree->op)==0)
		return(tree);
	if (op==NAME && tree->class==AUTO) {
		tree->class = OFFS;
		tree->regno = 5;
		tree->offset = tree->nloc;
	}
	dope = opdope[op];
	if ((dope&LEAF) != 0)
		return(tree);
	if ((dope&BINARY) == 0)
		return(unoptim(tree));
	/* is known to be binary */
	if (tree->type==CHAR)
		tree->type = INT;
	if ((dope&COMMUTE)!=0) {
	acomm:	d1 = tree->type;
		tree = acommute(tree);
		tree->type = d1;
		/*
		 * PDP-11 special:
		 * replace a&b by a NAND ~ b.
		 * This will be undone when in
		 * truth-value context.
		 */
		if (tree->op!=AND)
			return(tree);
		tree->op = NAND;
		tree->tr2 = block(1, COMPL, tree->tr2->type, 0, tree->tr2);
	}
    again:
	tree->tr1 = optim(tree->tr1);
	tree->tr2 = optim(tree->tr2);
	if ((dope&RELAT) != 0) {
		if ((d1=degree(tree->tr1)) < (d2=degree(tree->tr2))
		 || d1==d2 && tree->tr1->op==NAME && tree->tr2->op!=NAME) {
			t = tree->tr1;
			tree->tr1 = tree->tr2;
			tree->tr2 = t;
			tree->op = maprel[op-EQUAL];
		}
		if (tree->tr1->type==CHAR && tree->tr2->op==CON
		 && (dcalc(tree->tr1) <= 12 || tree->tr1->op==STAR)
		 && tree->tr2->value <= 127 && tree->tr2->value >= 0)
			tree->tr2->type = CHAR;
	}
	d1 = max(degree(tree->tr1), islong(tree->type));
	d2 = max(degree(tree->tr2), 0);
	if (tree->tr1->type==LONG && dope&RELAT)
		d1 = 10;
	switch (op) {

	case LTIMES:
	case LDIV:
	case LMOD:
	case LASTIMES:
	case LASDIV:
	case LASMOD:
		tree->degree = 10;
		break;

	/*
	 * PDP-11 special:
	 * generate new =&~ operator out of =&
	 * by complementing the RHS.
	 */
	case ASSAND:
		op = ASSNAND;
		tree->op = op;
		tree->tr2 = block(2, COMPL, tree->tr2->type, 0, tree->tr2);
		goto again;

	case NAND:
		if (isconstant(tree->tr2) && tree->tr2->value==0)
			return(tree->tr1);
		goto def;

	case CALL:
		tree->degree = 10;
		break;

	case QUEST:
	case COLON:
		tree->degree = max(d1, d2);
		break;

	case MINUS:
		if (t = isconstant(tree->tr2)) {
			tree->op = PLUS;
			if (t->type==DOUBLE)
				/* PDP-11 FP representation */
				t->value =^ 0100000;
			else
				t->value = -t->value;
			goto acomm;
		}
		goto def;

	case DIVIDE:
	case ASDIV:
	case ASTIMES:
		if (tree->tr2->op==CON && tree->tr2->value==1)
			return(tree->tr1);
		if (ispow2(tree) == 0) {

		case MOD:
		case ASMOD:
			d1 =+ 2;
			d2 =+ 2;
		}
		if (tree->type==LONG)
			return(hardlongs(tree));
		goto constant;

	case LSHIFT:
	case RSHIFT:
	case ASRSH:
	case ASLSH:
		if (tree->tr2->op==CON && tree->tr2->value==0)
			return(tree->tr1);
		/*
		 * PDP-11 special: turn right shifts into negative
		 * left shifts
		 */
		if (op==LSHIFT||op==ASLSH)
			goto constant;
		if (tree->tr2->op==CON && tree->tr2->value==1)
			goto constant;
		op =+ (LSHIFT-RSHIFT);
		tree->op = op;
		tree->tr2 = block(1, NEG, tree->type, 0, tree->tr2);
		goto again;

	constant:
		if (tree->tr1->op==CON && tree->tr2->op==CON) {
			const(op, &tree->tr1->value, tree->tr2->value);
			return(tree->tr1);
		}


	def:
	default:
		tree->degree = d1==d2? d1+islong(tree->type): max(d1, d2);
		break;
	}
	return(tree);
}

unoptim(atree)
struct tnode *atree;
{
	register struct tnode *subtre, *tree;
	register int *p;
	double static fv;
	struct { int integer; };

	if ((tree=atree)==0)
		return(0);
	if (tree->op==CBRANCH) {
		tree->btree = optim(tree->btree);
		return(tree);
	}
	subtre = tree->tr1 = optim(tree->tr1);
	switch (tree->op) {

	case FSEL:
		tree->tr1 = block(2, RSHIFT, INT, 0, subtre,
		    block(1, CON, INT, 0, tree->bitoffs));
		tree->op = AND;
		tree->type = INT;
		tree->tr2 = block(1, CON, INT, 0, (1<<tree->flen)-1);
		return(optim(tree));

	case AMPER:
		if (subtre->op==STAR)
			return(subtre->tr1);
		if (subtre->op==NAME && subtre->class == OFFS) {
			p = block(2, PLUS, tree->type, 1, subtre, tree);
			subtre->type = tree->type;
			tree->op = CON;
			tree->type = INT;
			tree->degree = 0;
			tree->value = subtre->offset;
			subtre->class = REG;
			subtre->nloc = subtre->regno;
			subtre->offset = 0;
			return(p);
		}
		break;

	case STAR:
		if (subtre->op==AMPER)
			return(subtre->tr1);
		if (subtre->op==NAME && subtre->class==REG) {
			subtre->type = tree->type;
			subtre->class = OFFS;
			subtre->regno = subtre->nloc;
			return(subtre);
		}
		p = subtre->tr1;
		if ((subtre->op==INCAFT||subtre->op==DECBEF)&&tree->type!=LONG
		 && p->op==NAME && p->class==REG && p->type==subtre->type) {
			p->type = tree->type;
			p->op = subtre->op==INCAFT? AUTOI: AUTOD;
			return(p);
		}
		if (subtre->op==PLUS && p->op==NAME && p->class==REG) {
			if (subtre->tr2->op==CON) {
				p->offset =+ subtre->tr2->value;
				p->class = OFFS;
				p->type = tree->type;
				p->regno = p->nloc;
				return(p);
			}
			if (subtre->tr2->op==AMPER) {
				subtre = subtre->tr2->tr1;
				subtre->class =+ XOFFS-EXTERN;
				subtre->regno = p->nloc;
				subtre->type = tree->type;
				return(subtre);
			}
		}
		break;
	case EXCLA:
		if ((opdope[subtre->op]&RELAT)==0)
			break;
		tree = subtre;
		tree->op = notrel[tree->op-EQUAL];
		break;

	case NEG:
	case COMPL:
		if (tree->type==CHAR)
			tree->type = INT;
		if (tree->op == subtre->op)
			return(subtre->tr1);
		if (subtre->op==ITOL) {
			subtre->op = tree->op;
			subtre->type = INT;
			tree->op = ITOL;
		}
	}
	if (subtre->op == CON) switch(tree->op) {

	case NEG:
		subtre->value = -subtre->value;
		return(subtre);

	case COMPL:
		subtre->value = ~subtre->value;
		return(subtre);

	case ITOF:
		fv = subtre->value;
		p = &fv;
		p++;
		if (*p++==0 && *p++==0 && *p++==0) {
			subtre->type = DOUBLE;
			subtre->value = fv.integer;
			subtre->op = SFCON;
			return(subtre);
		}
		break;
	}
	tree->degree = max(islong(tree->type), degree(subtre));
	return(tree);
}

struct acl {
	int nextl;
	int nextn;
	struct tnode *nlist[20];
	struct tnode *llist[21];
};

acommute(atree)
{
	struct acl acl;
	int d, i, op, flt;
	register struct tnode *t1, **t2, *tree;
	struct tnode *t;

	acl.nextl = 0;
	acl.nextn = 0;
	tree = atree;
	op = tree->op;
	flt = isfloat(tree);
	insert(op, tree, &acl);
	acl.nextl--;
	t2 = &acl.llist[acl.nextl];
	if (!flt) {
		/* put constants together */
		for (i=acl.nextl;i>0&&t2[0]->op==CON&&t2[-1]->op==CON;i--) {
			acl.nextl--;
			t2--;
			const(op, &t2[0]->value, t2[1]->value);
		}
	}
	if (op==PLUS || op==OR) {
		/* toss out "+0" */
		if (acl.nextl>0 && (t1 = isconstant(*t2)) && t1->value==0) {
			acl.nextl--;
			t2--;
		}
		if (acl.nextl <= 0)
			return(*t2);
		/* subsume constant in "&x+c" */
		if (op==PLUS && t2[0]->op==CON && t2[-1]->op==AMPER) {
			t2--;
			t2[0]->tr1->offset =+ t2[1]->value;
			acl.nextl--;
		}
	} else if (op==TIMES || op==AND) {
		t1 = acl.llist[acl.nextl];
		if (t1->op==CON) {
			if (t1->value==0)
				return(t1);
			if (op==TIMES && t1->value==1 && acl.nextl>0)
				if (--acl.nextl <= 0)
					return(acl.llist[0]);
		}
	}
	if (op==PLUS && !flt)
		distrib(&acl);
	tree = *(t2 = &acl.llist[0]);
	d = max(degree(tree), islong(tree->type));
	if (op==TIMES && !flt)
		d++;
	for (i=0; i<acl.nextl; i++) {
		t1 = acl.nlist[i];
		t1->tr2 = t = *++t2;
		t1->degree = d = d==degree(t)? d+islong(t1->type): max(d, degree(t));
		t1->tr1 = tree;
		tree = t1;
		if (tree->type==LONG) {
			if (tree->op==TIMES)
				tree = hardlongs(tree);
			else if (tree->op==PLUS && (t = isconstant(tree->tr1))
			       && t->value < 0) {
				tree->op = MINUS;
				t->value = - t->value;
				t = tree->tr1;
				tree->tr1 = tree->tr2;
				tree->tr2 = t;
			}
		}
	}
	if (tree->op==TIMES && ispow2(tree))
		tree->degree = max(degree(tree->tr1), islong(tree->type));
	return(tree);
}

distrib(list)
struct acl *list;
{
/*
 * Find a list member of the form c1c2*x such
 * that c1c2 divides no other such constant, is divided by
 * at least one other (say in the form c1*y), and which has
 * fewest divisors. Reduce this pair to c1*(y+c2*x)
 * and iterate until no reductions occur.
 */
	register struct tnode **p1, **p2;
	struct tnode *t;
	int ndmaj, ndmin;
	struct tnode **dividend, **divisor;
	struct tnode **maxnod, **mindiv;

    loop:
	maxnod = &list->llist[list->nextl];
	ndmaj = 1000;
	dividend = 0;
	for (p1 = list->llist; p1 <= maxnod; p1++) {
		if ((*p1)->op!=TIMES || (*p1)->tr2->op!=CON)
			continue;
		ndmin = 0;
		for (p2 = list->llist; p2 <= maxnod; p2++) {
			if (p1==p2 || (*p2)->op!=TIMES || (*p2)->tr2->op!=CON)
				continue;
			if ((*p1)->tr2->value == (*p2)->tr2->value) {
				(*p2)->tr2 = (*p1)->tr1;
				(*p2)->op = PLUS;
				(*p1)->tr1 = (*p2);
				*p1 = optim(*p1);
				squash(p2, maxnod);
				list->nextl--;
				goto loop;
			}
			if (((*p2)->tr2->value % (*p1)->tr2->value) == 0)
				goto contmaj;
			if (((*p1)->tr2->value % (*p2)->tr2->value) == 0) {
				ndmin++;
				mindiv = p2;
			}
		}
		if (ndmin > 0 && ndmin < ndmaj) {
			ndmaj = ndmin;
			dividend = p1;
			divisor = mindiv;
		}
    contmaj:;
	}
	if (dividend==0)
		return;
	t = list->nlist[--list->nextn];
	p1 = dividend;
	p2 = divisor;
	t->op = PLUS;
	t->type = (*p1)->type;
	t->tr1 = (*p1);
	t->tr2 = (*p2)->tr1;
	(*p1)->tr2->value =/ (*p2)->tr2->value;
	(*p2)->tr1 = t;
	t = optim(*p2);
	if (p1 < p2) {
		*p1 = t;
		squash(p2, maxnod);
	} else {
		*p2 = t;
		squash(p1, maxnod);
	}
	list->nextl--;
	goto loop;
}

squash(p, maxp)
struct tnode **p, **maxp;
{
	register struct tnode **np;

	for (np = p; np < maxp; np++)
		*np = *(np+1);
}

const(op, vp, av)
int *vp;
{
	register int v;

	v = av;
	switch (op) {

	case PLUS:
		*vp =+ v;
		return;

	case TIMES:
		*vp =* v;
		return;

	case AND:
		*vp =& v;
		return;

	case OR:
		*vp =| v;
		return;

	case EXOR:
		*vp =^ v;
		return;

	case DIVIDE:
	case MOD:
		if (v==0)
			error("Divide check");
		else
			if (op==DIVIDE)
				*vp =/ v;
			else
				*vp =% v;
		return;

	case RSHIFT:
		*vp =>> v;
		return;

	case LSHIFT:
		*vp =<< v;
		return;

	case NAND:
		*vp =& ~ v;
		return;
	}
	error("C error: const");
}

insert(op, atree, alist)
struct acl *alist;
{
	register d;
	register struct acl *list;
	register struct tnode *tree;
	int d1, i;
	struct tnode *t;

	tree = atree;
	list = alist;
	if (tree->op == op) {
	ins:	list->nlist[list->nextn++] = tree;
		insert(op, tree->tr1, list);
		insert(op, tree->tr2, list);
		return;
	}
	tree = optim(tree);
	if (tree->op == op)
		goto ins;
	if (!isfloat(tree)) {
		/* c1*(x+c2) -> c1*x+c1*c2 */
		if ((tree->op==TIMES||tree->op==LSHIFT)
		  && tree->tr2->op==CON && tree->tr2->value>0
		  && tree->tr1->op==PLUS && tree->tr1->tr2->op==CON) {
			d = tree->tr2->value;
			if (tree->op==TIMES)
				tree->tr2->value =* tree->tr1->tr2->value;
			else
				tree->tr2->value = tree->tr1->tr2->value << d;
			tree->tr1->tr2->value = d;
			tree->tr1->op = tree->op;
			tree->op = PLUS;
			if (op==PLUS)
				goto ins;
		}
	}
	d = degree(tree);
	for (i=0; i<list->nextl; i++) {
		if ((d1=degree(list->llist[i]))<d) {
			t = list->llist[i];
			list->llist[i] = tree;
			tree = t;
			d = d1;
		}
	}
	list->llist[list->nextl++] = tree;
}

block(an, args)
{
	register int *p;
	int *oldp;
	register *argp, n;

	oldp = p = spacep;
	n = an+3;
	argp = &args;
	do
		*p++ = *argp++;
	while (--n);
	if (p >= &treespace[ossiz]) {
		error("Exp. ov. pass 2");
		exit(1);
	}
	spacep = p;
	return(oldp);
}

islong(t)
{
	if (t==LONG)
		return(2);
	return(1);
}

isconstant(at)
struct tnode *at;
{
	register struct tnode *t;

	t = at;
	if (t->op==CON || t->op==SFCON)
		return(t);
	if (t->op==ITOL && t->tr1->op==CON)
		return(t->tr1);
	return(0);
}

hardlongs(at)
struct tnode *at;
{
	register struct tnode *t;

	t = at;
	switch(t->op) {

	case TIMES:
	case DIVIDE:
	case MOD:
		t->op =+ LTIMES-TIMES;
		break;

	case ASTIMES:
	case ASDIV:
	case ASMOD:
		t->op =+ LASTIMES-ASTIMES;
		t->tr1 = block(1, AMPER, LONG+PTR, 0, t->tr1);
		break;

	default:
		return(t);
	}
	return(optim(t));
}
int opdope[] {
	000000,	/* EOF */
	000000,	/* ; */
	000000,	/* { */
	000000,	/* } */
	036000,	/* [ */
	002000,	/* ] */
	036000,	/* ( */
	002000,	/* ) */
	014201,	/* : */
	007001,	/* , */
	000000,	/* field selection */
	000000,	/* 11 */
	000000,	/* 12 */
	000000,	/* 13 */
	000000,	/* 14 */
	000000,	/* 15 */
	000000,	/* 16 */
	000000,	/* 17 */
	000000,	/* 18 */
	000000,	/* 19 */
	000400,	/* name */
	000400,	/* short constant */
	000400,	/* string */
	000400,	/* float */
	000400,	/* double */
	000000,	/* 25 */
	000000,	/* 26 */
	000400,	/* autoi, *r++ */
	000400,	/* autod, *--r */
	000000,	/* 29 */
	034203,	/* ++pre */
	034203,	/* --pre */
	034203,	/* ++post */
	034203,	/* --post */
	034220,	/* !un */
	034202,	/* &un */
	034220,	/* *un */
	034200,	/* -un */
	034220,	/* ~un */
	036001,	/* . (structure reference) */
	030101,	/* + */
	030001,	/* - */
	032101,	/* * */
	032001,	/* / */
	032001,	/* % */
	026061,	/* >> */
	026061,	/* << */
	020161,	/* & */
	016161,	/* | */
	016161,	/* ^ */
	036001,	/* -> */
	001000,	/* int -> double */
	001000,	/* double -> int */
	000001,	/* && */
	000001,	/* || */
	030001, /* &~ */
	001000,	/* double -> long */
	001000,	/* long -> double */
	001000,	/* integer -> long */
	001000,	/* long -> integer */
	022005,	/* == */
	022005,	/* != */
	024005,	/* <= */
	024005,	/* < */
	024005,	/* >= */
	024005,	/* > */
	024005,	/* <p */
	024005,	/* <=p */
	024005,	/* >p */
	024005,	/* >=p */
	012213,	/* =+ */
	012213,	/* =- */
	012213,	/* =* */
	012213,	/* =/ */
	012213,	/* =% */
	012253,	/* =>> */
	012253,	/* =<< */
	012253,	/* =& */
	012253,	/* =| */
	012253,	/* =^ */
	012213,	/* = */
	030001, /* & for tests */
	032101,	/*  * (long) */
	032001,	/*  / (long) */
	032001,	/* % (long) */
	012253,	/* =& ~ */
	012213,	/* =* (long) */
	012213,	/* / (long) */
	012213,	/* % (long) */
	000000,	/* 89 */
	014201,	/* ? */
	026061,	/* long << */
	012253,	/* long =<< */
	000000,	/* 93 */
	000000,	/* 94 */
	000000,	/* 95 */
	000000,	/* 96 */
	000000,	/* 97 */
	000000,	/* 98 */
	000000,	/* 99 */
	036001,	/* call */
	036000,	/* mcall */
	000000,	/* goto */
	000000,	/* jump cond */
	000000,	/* branch cond */
	000400,	/* set nregs */
	000000, /* 106 */
	000000,	/* 107 */
	000000,	/* 108 */
	000000,	/* 109 */
	000000	/* force r0 */
};

char	*opntab[] {
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	":",
	",",
	"field select",
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	0,
	"name",
	"short constant",
	"string",
	"float",
	"double",
	0,
	0,
	"*r++",
	"*--r",
	0,
	"++pre",
	"--pre",
	"++post",
	"--post",
	"!un",
	"&",
	"*",
	"-",
	"~",
	".",
	"+",
	"-",
	"*",
	"/",
	"%",
	">>",
	"<<",
	"&",
	"|",
	"^",
	"->",
	"int->double",
	"double->int",
	"&&",
	"||",
	"&~",
	"double->long",
	"long->double",
	"integer->long",
	"long->integer",
	"==",
	"!=",
	"<=",
	"<",
	">=",
	">",
	"<p",
	"<=p",
	">p",
	">=p",
	"=+",
	"=-",
	"=*",
	"=/",
	"=%",
	"=>>",
	"=<<",
	"=&",
	"=|",
	"=^",
	"=",
	"& for tests",
	"*",
	"/",
	"%",
	"=& ~",
	"=*",
	"=/",
	"=%",
	0,
	"?",
	"<<",
	"=<<",
	0,
	0,
	0,
	0,
	0,
	"call",
	"call",
	"call",
	0,
	"goto",
	"jump cond",
	"branch cond",
	"set nregs",
	"load value",
	0,
	0,
	0,
	"force register"
};
