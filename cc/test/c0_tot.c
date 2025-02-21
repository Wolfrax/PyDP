#
/* C compiler
 *
 *
 *
 * Called from cc:
 *   c0 source temp1 temp2 [ profileflag ]
 * temp1 contains some ascii text and the binary expression
 * trees.  Each tree is introduced by the # character.
 * Strings are put on temp2, which cc tacks onto
 * temp1 for assembly.
 */

#include "c0h.c"

int	isn	1;
int	stflg	1;
int	peeksym	-1;
int	line	1;
int	debug	0;
int	dimp	0;
struct	tname	funcblk { NAME, 0, 0, REG, 0, 0 };
int	*treespace { osspace };

struct kwtab {
	char	*kwname;
	int	kwval;
} kwtab[]
{
	"int",		INT,
	"char",		CHAR,
	"float",	FLOAT,
	"double",	DOUBLE,
	"struct",	STRUCT,
	"long",		LONG,
	"auto",		AUTO,
	"extern",	EXTERN,
	"static",	STATIC,
	"register",	REG,
	"goto",		GOTO,
	"return",	RETURN,
	"if",		IF,
	"while",	WHILE,
	"else",		ELSE,
	"switch",	SWITCH,
	"case",		CASE,
	"break",	BREAK,
	"continue",	CONTIN,
	"do",		DO,
	"default",	DEFAULT,
	"for",		FOR,
	"sizeof",	SIZEOF,
	0,		0,
};

main(argc, argv)
char *argv[];
{
	extern fin;
	register char *sp;
	register i;
	register struct kwtab *ip;

	if(argc<3) {
		error("Arg count");
		exit(1);
	}
	if((fin=open(argv[1],0))<0) {
		error("Can't find %s", argv[1]);
		exit(1);
	}
	if (fcreat(argv[2], obuf)<0 || fcreat(argv[3], sbuf)<0) {
		error("Can't create temp");
		exit(1);
	}
	if (argc>4)
		proflg++;
	/*
	 * The hash table locations of the keywords
	 * are marked; if an identifier hashes to one of
	 * these locations, it is looked up in in the keyword
	 * table first.
	 */
	for (ip=kwtab; (sp = ip->kwname); ip++) {
		i = 0;
		while (*sp)
			i =+ *sp++;
		hshtab[i%hshsiz].hflag = FKEYW;
	}
	while(!eof) {
		extdef();
		blkend();
	}
	outcode("B", EOF);
	strflg++;
	outcode("B", EOF);
	fflush(obuf);
	fflush(sbuf);
	exit(nerror!=0);
}

/*
 * Look up the identifier in symbuf in the symbol table.
 * If it hashes to the same spot as a keyword, try the keyword table
 * first.  An initial "." is ignored in the hash.
 * Return is a ptr to the symbol table entry.
 */
lookup()
{
	int ihash;
	register struct hshtab *rp;
	register char *sp, *np;

	ihash = 0;
	sp = symbuf;
	if (*sp=='.')
		sp++;
	while (sp<symbuf+ncps)
		ihash =+ *sp++;
	rp = &hshtab[ihash%hshsiz];
	if (rp->hflag&FKEYW)
		if (findkw())
			return(KEYW);
	while (*(np = rp->name)) {
		for (sp=symbuf; sp<symbuf+ncps;)
			if (*np++ != *sp++)
				goto no;
		csym = rp;
		return(NAME);
	no:
		if (++rp >= &hshtab[hshsiz])
			rp = hshtab;
	}
	if(++hshused >= hshsiz) {
		error("Symbol table overflow");
		exit(1);
	}
	rp->hclass = 0;
	rp->htype = 0;
	rp->hoffset = 0;
	rp->dimp = 0;
	rp->hflag =| xdflg;
	sp = symbuf;
	for (np=rp->name; sp<symbuf+ncps;)
		*np++ = *sp++;
	csym = rp;
	return(NAME);
}

/*
 * Search the keyword table.
 * Ignore initial "." to avoid member-of-structure
 * problems.
 */
findkw()
{
	register struct kwtab *kp;
	register char *p1, *p2;
	char *wp;

	wp = symbuf;
	if (*wp=='.')
		wp++;
	for (kp=kwtab; (p2 = kp->kwname); kp++) {
		p1 = wp;
		while (*p1 == *p2++)
			if (*p1++ == '\0') {
				cval = kp->kwval;
				return(1);
			}
	}
	return(0);
}


/*
 * Return the next symbol from the input.
 * peeksym is a pushed-back symbol, peekc is a pushed-back
 * character (after peeksym).
 * mosflg means that the next symbol, if an identifier,
 * is a member of structure or a structure tag, and it
 * gets a "." prepended to it to distinguish
 * it from other identifiers.
 */
symbol() {
	register c;
	register char *sp;

	if (peeksym>=0) {
		c = peeksym;
		peeksym = -1;
		if (c==NAME)
			mosflg = 0;
		return(c);
	}
	if (peekc) {
		c = peekc;
		peekc = 0;
	} else
		if (eof)
			return(EOF);
		else
			c = getchar();
loop:
	switch(ctab[c]) {

	case INSERT:		/* ignore newlines */
		inhdr = 1;
		c = getchar();
		goto loop;

	case NEWLN:
		if (!inhdr)
			line++;
		inhdr = 0;

	case SPACE:
		c = getchar();
		goto loop;

	case EOF:
		eof++;
		return(0);

	case PLUS:
		return(subseq(c,PLUS,INCBEF));

	case MINUS:
		return(subseq(c,subseq('>',MINUS,ARROW),DECBEF));

	case ASSIGN:
		if (subseq(' ',0,1)) return(ASSIGN);
		c = symbol();
		if (c>=PLUS && c<=EXOR) {
			if (spnextchar() != ' '
			 && (c==MINUS || c==AND || c==TIMES)) {
				error("Warning: assignment operator assumed");
				nerror--;
			}
			return(c+ASPLUS-PLUS);
		}
		if (c==ASSIGN)
			return(EQUAL);
		peeksym = c;
		return(ASSIGN);

	case LESS:
		if (subseq(c,0,1)) return(LSHIFT);
		return(subseq('=',LESS,LESSEQ));

	case GREAT:
		if (subseq(c,0,1)) return(RSHIFT);
		return(subseq('=',GREAT,GREATEQ));

	case EXCLA:
		return(subseq('=',EXCLA,NEQUAL));

	case DIVIDE:
		if (subseq('*',1,0))
			return(DIVIDE);
		while ((c = spnextchar()) != EOF) {
			peekc = 0;
			if (c=='*') {
				if (spnextchar() == '/') {
					peekc = 0;
					c = getchar();
					goto loop;
				}
			}
		}
		eof++;
			error("Nonterminated comment");
			return(0);

	case PERIOD:
	case DIGIT:
		peekc = c;
		if ((c=getnum(c=='0'?8:10)) == FCON)
			cval = isn++;
		return(c);

	case DQUOTE:
		return(getstr());

	case SQUOTE:
		return(getcc());

	case LETTER:
		sp = symbuf;
		if (mosflg) {
			*sp++ = '.';
			mosflg = 0;
		}
		while(ctab[c]==LETTER || ctab[c]==DIGIT) {
			if (sp<symbuf+ncps) *sp++ = c;
			c = getchar();
		}
		while(sp<symbuf+ncps)
			*sp++ = '\0';
		peekc = c;
		if ((c=lookup())==KEYW && cval==SIZEOF)
			c = SIZEOF;
		return(c);

	case AND:
		return(subseq('&', AND, LOGAND));

	case OR:
		return(subseq('|', OR, LOGOR));

	case UNKN:
		error("Unknown character");
		c = getchar();
		goto loop;

	}
	return(ctab[c]);
}

/*
 * If the next input character is c, return a and advance.
 * Otherwise push back the character and return a.
 */
subseq(c,a,b)
{
	if (spnextchar() != c)
		return(a);
	peekc = 0;
	return(b);
}

/*
 * Read a double-quoted string, placing it on the
 * string buffer.
 */
getstr()
{
	register int c;
	register char *sp;

	nchstr = 1;
	sp = savstr;
	while((c=mapch('"')) >= 0) {
		nchstr++;
		if (sp >= &savstr[STRSIZ]) {
			sp = savstr;
			error("String too long");
		}
		*sp++ = c;
	}
	strptr = sp;
	cval = isn++;
	return(STRING);
}

/*
 * Write out a string, either in-line
 * or in the string temp file labelled by
 * lab.
 */
putstr(lab)
{
	register char *sp;

	if (lab) {
		strflg++;
		outcode("BNB", LABEL, lab, BDATA);
	} else
		outcode("B", BDATA);
	for (sp = savstr; sp<strptr; )
		outcode("1N", *sp++ & 0377);
	outcode("100");
	strflg = 0;
}

/*
 * read a single-quoted character constant.
 * The routine is sensitive to the layout of
 * characters in a word.
 */
getcc()
{
	register int c, cc;
	register char *ccp;

	cval = 0;
	ccp = &cval;
	cc = 0;
	while((c=mapch('\'')) >= 0)
		if(cc++ < NCPW)
			*ccp++ = c;
	if(cc>NCPW)
		error("Long character constant");
	return(CON);
}

/*
 * Read a character in a string or character constant,
 * detecting the end of the string.
 * It implements the escape sequences.
 */
mapch(ac)
{
	register int a, c, n;
	static mpeek;

	c = ac;
	if (a = mpeek)
		mpeek = 0;
	else
		a = getchar();
loop:
	if (a==c)
		return(-1);
	switch(a) {

	case '\n':
	case '\0':
		error("Nonterminated string");
		peekc = a;
		return(-1);

	case '\\':
		switch (a=getchar()) {

		case 't':
			return('\t');

		case 'n':
			return('\n');

		case 'b':
			return('\b');

		case '0': case '1': case '2': case '3':
		case '4': case '5': case '6': case '7':
			n = 0;
			c = 0;
			while (++c<=3 && '0'<=a && a<='7') {
				n =<< 3;
				n =+ a-'0';
				a = getchar();
			}
			mpeek = a;
			return(n);

		case 'r':
			return('\r');

		case '\n':
			if (!inhdr)
				line++;
			inhdr = 0;
			a = getchar();
			goto loop;
		}
	}
	return(a);
}

/*
 * Read an expression and return a pointer to its tree.
 * It's the classical bottom-up, priority-driven scheme.
 * The initflg prevents the parse from going past
 * "," or ":" because those delimitesrs are special
 * in initializer (and some other) expressions.
 */
tree()
{
#define	SEOF	200
#define	SSIZE	20
	int *op, opst[SSIZE], *pp, prst[SSIZE];
	register int andflg, o;
	register struct hshtab *cs;
	int p, ps, os;

	space = treespace;
	op = opst;
	pp = prst;
	cp = cmst;
	*op = SEOF;
	*pp = 06;
	andflg = 0;

advanc:
	switch (o=symbol()) {

	case NAME:
		cs = csym;
		if (cs->hclass==0 && cs->htype==0)
			if(nextchar()=='(') {
				/* set function */
				cs->hclass = EXTERN;
				cs->htype = FUNC;
			} else if (initflg)
				cs->hclass = EXTERN;
			else {
				/* set label */
				cs->htype = ARRAY;
				if (cs->hoffset==0)
					cs->hoffset = isn++;
			}
		*cp++ = copname(cs);
		goto tand;

	case FCON:
		if (!initflg)
			outcode("BBNB1N1N1N1N0B", DATA,LABEL,
			    cval, WDATA, fcval, PROG);

	case CON:
	case SFCON:
		*cp++ = block(1,o,(o==CON?INT:DOUBLE),0,cval);
		goto tand;

	/* fake a static char array */
	case STRING:
		putstr(cval);
		*cp++ = block(3, NAME, ARRAY+CHAR,0,STATIC,0,cval);

tand:
		if(cp>=cmst+cmsiz) {
			error("Expression overflow");
			exit(1);
		}
		if (andflg)
			goto syntax;
		andflg = 1;
		goto advanc;

	case INCBEF:
	case DECBEF:
		if (andflg)
			o =+ 2;
		goto oponst;

	case COMPL:
	case EXCLA:
	case SIZEOF:
		if (andflg)
			goto syntax;
		goto oponst;

	case MINUS:
		if (!andflg)  {
			if ((peeksym=symbol())==FCON) {
				fcval = - fcval;
				goto advanc;
			}
			if (peeksym==SFCON) {
				fcval = - fcval;
				cval =^ 0100000;
				goto advanc;
			}
			o = NEG;
		}
		andflg = 0;
		goto oponst;

	case AND:
	case TIMES:
		if (andflg)
			andflg = 0; else
			if(o==AND)
				o = AMPER;
			else
				o = STAR;
		goto oponst;

	case LPARN:
		if (andflg) {
			o = symbol();
			if (o==RPARN)
				o = MCALL;
			else {
				peeksym = o;
				o = CALL;
				andflg = 0;
			}
		}
		goto oponst;

	case RBRACK:
	case RPARN:
		if (!andflg)
			goto syntax;
		goto oponst;

	case DOT:
	case ARROW:
		mosflg++;
		break;

	}
	/* binaries */
	if (!andflg)
		goto syntax;
	andflg = 0;

oponst:
	p = (opdope[o]>>9) & 077;
	if ((o==COMMA || o==COLON) && initflg)
		p = 05;
opon1:
	ps = *pp;
	if (p>ps || p==ps && (opdope[o]&RASSOC)!=0) {
		switch (o) {

		case INCAFT:
		case DECAFT:
			p = 37;
			break;
		case LPARN:
		case LBRACK:
		case CALL:
			p = 04;
		}
		if (op >= &opst[SSIZE-1]) {
			error("expression overflow");
			exit(1);
		}
		*++op = o;
		*++pp = p;
		goto advanc;
	}
	--pp;
	switch (os = *op--) {

	case SEOF:
		peeksym = o;
		build(0);		/* flush conversions */
		return(*--cp);

	case CALL:
		if (o!=RPARN)
			goto syntax;
		build(os);
		goto advanc;

	case MCALL:
		*cp++ = block(0,0,0,0);	/* 0 arg call */
		os = CALL;
		break;

	case INCBEF:
	case INCAFT:
	case DECBEF:
	case DECAFT:
		*cp++ = block(1, CON, INT, 0, 1);
		break;

	case LPARN:
		if (o!=RPARN)
			goto syntax;
		goto advanc;

	case LBRACK:
		if (o!=RBRACK)
			goto syntax;
		build(LBRACK);
		goto advanc;
	}
	build(os);
	goto opon1;

syntax:
	error("Expression syntax");
	errflush(o);
	return(0);
}

/*
 * Generate a tree node for a name.
 * All the relevant info from the symbol table is
 * copied out, including the name if it's an external.
 * This is because the symbol table is gone in the next
 * pass, so a ptr isn't sufficient.
 */
copname(acs)
struct hshtab *acs;
{
	register struct hshtab *cs;
	register struct tname *tp;
	register char *cp1;
	int i;
	char *cp2;

	cs = acs;
	tp = gblock(sizeof(*tp)/NCPW);
	tp->op = NAME;
	tp->type = cs->htype;
	tp->dimp = cs->hdimp;
	if ((tp->class = cs->hclass)==0)
		tp->class = STATIC;
	tp->offset = 0;
	tp->nloc = cs->hoffset;
	if (cs->hclass==EXTERN) {
		gblock((ncps-NCPW)/NCPW);
		cp1 = tp->nname;
		cp2 = cs->name;
		i = ncps;
		do {
			*cp1++ = *cp2++;
		} while (--i);
	}
	if (cs->hflag&FFIELD)
		tp->class = FMOS;
	return(tp);
}
#
/*
 * C compiler
 *
 *
 */

#include "c0h.c"

/*
 * Called from tree, this routine takes the top 1, 2, or 3
 * operands on the expression stack, makes a new node with
 * the operator op, and puts it on the stack.
 * Essentially all the work is in inserting
 * appropriate conversions.
 */
build(op) {
	register int t1;
	int t2, t3, t;
	struct tnode *p3, *disarray();
	register struct tnode *p1, *p2;
	int d, dope, leftc, cvn, pcvn;

	/*
	 * a[i] => *(a+i)
	 */
	if (op==LBRACK) {
		build(PLUS);
		op = STAR;
	}
	dope = opdope[op];
	if ((dope&BINARY)!=0) {
		p2 = chkfun(disarray(*--cp));
		t2 = p2->type;
	}
	p1 = *--cp;
	/*
	 * sizeof gets turned into a number here.
	 * Bug: sizeof(structure-member-array) is 2 because
	 * the array has been turned into a ptr already.
	 */
	if (op==SIZEOF) {
		t1 = length(p1);
		p1->op = CON;
		p1->type = INT;
		p1->dimp = 0;
		p1->value = t1;
		*cp++ = p1;
		return;
	}
	if (op!=AMPER) {
		p1 = disarray(p1);
		if (op!=CALL)
			p1 = chkfun(p1);
	}
	t1 = p1->type;
	pcvn = 0;
	t = INT;
	switch (op) {

	/* end of expression */
	case 0:
		*cp++ = p1;
		return;

	/* no-conversion operators */
	case QUEST:
		if (p2->op!=COLON)
			error("Illegal conditional");
		t = t2;

	case COMMA:
	case LOGAND:
	case LOGOR:
		*cp++ = block(2, op, t, 0, p1, p2);
		return;

	case CALL:
		if ((t1&XTYPE) != FUNC)
			error("Call of non-function");
		*cp++ = block(2,CALL,decref(t1),p1->dimp,p1,p2);
		return;

	case STAR:
		if (p1->op==AMPER ) {
			*cp++ = p1->tr1;
			return;
		}
		if ((t1&XTYPE) == FUNC)
			error("Illegal indirection");
		*cp++ = block(1,STAR,decref(t1),p1->dimp,p1);
		return;

	case AMPER:
		if (p1->op==STAR) {
			p1->tr1->dimp = p1->dimp;
			p1->tr1->type = incref(t1);
			*cp++ = p1->tr1;
			return;
		}
		if (p1->op==NAME) {
			*cp++ = block(1,op,incref(t1),p1->dimp,p1);
			return;
		}
		error("Illegal lvalue");
		break;

	/*
	 * a->b goes to (*a).b
	 */
	case ARROW:
		*cp++ = p1;
		chkw(p1, -1);
		p1->type = PTR+STRUCT;
		build(STAR);
		p1 = *--cp;

	/*
	 * In a.b, a fairly complicated process has to
	 * be used to make the left operand look
	 * as if it had the type of the second.
	 * Also, the offset in the structure has to be
	 * given a special type to prevent conversion.
	 */
	case DOT:
		if (p2->op!=NAME || (p2->class!=MOS && p2->class!=FMOS))
			error("Illegal structure ref");
		*cp++ = p1;
		t = t2;
		if ((t&XTYPE) == ARRAY) {
			t = decref(t);
			p2->ssp++;
		}
		setype(p1, t, p2->dimp);
		build(AMPER);
		*cp++ = block(1,CON,NOTYPE,0,p2->nloc);
		build(PLUS);
		if ((t2&XTYPE) != ARRAY)
			build(STAR);
		if (p2->class == FMOS)
			*cp++ = block(2, FSEL, t, 0, *--cp, p2->dimp);
		return;
	}
	if ((dope&LVALUE)!=0)
		chklval(p1);
	if ((dope&LWORD)!=0)
		chkw(p1, LONG);
	if ((dope&RWORD)!=0)
		chkw(p2, LONG);
	if ((dope&BINARY)==0) {
		if (op==ITOF)
			t1 = DOUBLE;
		else if (op==FTOI)
			t1 = INT;
		if (!fold(op, p1, 0))
			*cp++ = block(1,op,t1,p1->dimp,p1);
		return;
	}
	cvn = 0;
	if (t1==STRUCT || t2==STRUCT) {
		error("Unimplemented structure operation");
		t1 = t2 = INT;
	}
	if (t2==NOTYPE) {
		t = t1;
		p2->type = INT;	/* no int cv for struct */
		t2 = INT;
	} else
		cvn = cvtab[lintyp(t1)][lintyp(t2)];
	leftc = (cvn>>4)&017;
	cvn =& 017;
	t = leftc? t2:t1;
	if (dope&ASSGOP) {
		t = t1;
		if (op==ASSIGN && (cvn==ITP||cvn==PTI))
			cvn = leftc = 0;
		if (leftc)
			cvn = leftc;
		leftc = 0;
	} else if (op==COLON && t1>=PTR && t1==t2)
		cvn = 0;
	else if (dope&RELAT) {
		if (op>=LESSEQ && (t1>=PTR || t2>=PTR))
			op =+ LESSEQP-LESSEQ;
		if (cvn==PTI)
			cvn = 0;
	}
	if (cvn==PTI) {
		cvn = 0;
		if (op==MINUS) {
			t = INT;
			pcvn++;
		} else {
			if (t1!=t2 || t1!=(PTR+CHAR))
				cvn = XX;
		}
	}
	if (cvn) {
		t1 = plength(p1);
		t2 = plength(p2);
		if (cvn==XX || (cvn==PTI&&t1!=t2))
			error("Illegal conversion");
		else if (leftc)
			p1 = convert(p1, t, cvn, t2);
		else
			p2 = convert(p2, t, cvn, t1);
	}
	if (dope&RELAT)
		t = INT;
	if (fold(op, p1, p2)==0)
		*cp++ = block(2,op,t,(p1->dimp==0? p2:p1)->dimp,p1,p2);
	if (pcvn && t1!=(PTR+CHAR)) {
		p1 = *--cp;
		*cp++ = convert(p1, 0, PTI, plength(p1->tr1));
	}
}

/*
 * Generate the appropirate conversion operator.
 * For pointer <=> integer this is a multiplication
 * or division, otherwise a special operator.
 */
convert(p, t, cvn, len)
struct tnode *p;
{
	register int n;

	switch(cvn) {

	case PTI:
	case ITP:
		if (len==1)
			return(p);
		return(block(2, (cvn==PTI?DIVIDE:TIMES), t, 0, p,
			block(1, CON, 0, 0, len)));

	case ITF:
		n = ITOF;
		break;
	case FTI:
		n = FTOI;
		break;
	case ITL:
		n = ITOL;
		break;
	case LTI:
		n = LTOI;
		break;
	case FTL:
		n = FTOL;
		break;
	case LTF:
		n = LTOF;
		break;
	}
	return(block(1, n, t, 0, p));
}

/*
 * Traverse an expression tree, adjust things
 * so the types of things in it are consistent
 * with the view that its top node has
 * type at.
 * Used with structure references.
 */
setype(ap, at, adimptr)
struct tnode *ap;
{
	register struct tnode *p;
	register t, dimptr;

	p = ap;
	t = at;
	dimptr = adimptr;
	p->type = t;
	if (dimptr != -1)
		p->dimp = dimptr;
	switch(p->op) {

	case AMPER:
		setype(p->tr1, decref(t), dimptr);
		return;

	case STAR:
		setype(p->tr1, incref(t), dimptr);
		return;

	case PLUS:
	case MINUS:
		setype(p->tr1, t, dimptr);
	}
}

/*
 * A mention of a function name is turned into
 * a pointer to that function.
 */
chkfun(ap)
struct tnode *ap;
{
	register struct tnode *p;
	register int t;

	p = ap;
	if (((t = p->type)&XTYPE)==FUNC)
		return(block(1,AMPER,incref(t),p->dimp,p));
	return(p);
}

/*
 * A mention of an array is turned into
 * a pointer to the base of the array.
 */
struct tnode *disarray(ap)
struct tnode *ap;
{
	register int t;
	register struct tnode *p;

	p = ap;
	/* check array & not MOS */
	if (((t = p->type)&XTYPE)!=ARRAY || p->op==NAME&&p->class==MOS)
		return(p);
	p->ssp++;
	*cp++ = p;
	setype(p, decref(t), -1);
	build(AMPER);
	return(*--cp);
}

/*
 * make sure that p is a ptr to a node
 * with type int or char or 'okt.'
 * okt might be nonexistent or 'long'
 * (e.g. for <<).
 */
chkw(p, okt)
struct tnode *p;
{
	register int t;

	if ((t=p->type)>CHAR && t<PTR && t!=okt)
		error("Integer operand required");
	return;
}

/*
 *'linearize' a type for looking up in the
 * conversion table
 */
lintyp(t)
{
	switch(t) {

	case INT:
	case CHAR:
		return(0);

	case FLOAT:
	case DOUBLE:
		return(1);

	case LONG:
		return(2);

	default:
		return(3);
	}
}

/*
 * Report an error.
 */
error(s, p1, p2, p3, p4, p5, p6)
{
	nerror++;
	printf("%d: ", line);
	printf(s, p1, p2, p3, p4, p5, p6);
	printf("\n");
}

/*
 * Generate a node in an expression tree,
 * setting the operator, type, degree (unused in this pass)
 * and the operands.
 */
block(an, op, t, d, p1,p2,p3)
int *p1, *p2, *p3;
{
	register int *ap, *p, n;
	int *oldp;

	n = an+3;
	p = gblock(n);
	oldp = p;
	ap = &op;
	do {
		*p++ = *ap++;
	} while (--n);
	return(oldp);
}

/*
 * Assign an unitialized block for use in the
 * expression tree.
 */
gblock(n)
{
	register int *p;

	p = space;
	if ((space =+ n) >= &osspace[OSSIZ]) {
		error("Expression overflow");
		exit(1);
	}
	return(p);
}

/*
 * Check that a tree can be used as an lvalue.
 */
chklval(ap)
struct tnode *ap;
{
	register struct tnode *p;

	p = ap;
	if (p->op!=NAME && p->op!=STAR)
		error("Lvalue required");
}

/*
 * reduce some forms of `constant op constant'
 * to a constant.  More of this is done in the next pass
 * but this is used to allow constant expressions
 * to be used in switches and array bounds.
 */
fold(op, ap1, ap2)
struct tnode *ap1, *ap2;
{
	register struct tnode *p1;
	register int v1, v2;

	p1 = ap1;
	if (p1->op!=CON || (ap2!=0 && ap2->op!=CON))
		return(0);
	v1 = p1->value;
	v2 = ap2->value;
	switch (op) {

	case PLUS:
		v1 =+ v2;
		break;

	case MINUS:
		v1 =- v2;
		break;

	case TIMES:
		v1 =* v2;
		break;

	case DIVIDE:
		v1 =/ v2;
		break;

	case MOD:
		v1 =% v2;
		break;

	case AND:
		v1 =& v2;
		break;

	case OR:
		v1 =| v2;
		break;

	case EXOR:
		v1 =^ v2;
		break;

	case NEG:
		v1 = - v1;
		break;

	case COMPL:
		v1 = ~ v1;
		break;

	case LSHIFT:
		v1 =<< v2;
		break;

	case RSHIFT:
		v1 =>> v2;
		break;

	default:
		return(0);
	}
	p1->value = v1;
	*cp++ = p1;
	return(1);
}

/*
 * Compile an expression expected to have constant value,
 * for example an array bound or a case value.
 */
conexp()
{
	register struct tnode *t;

	initflg++;
	if (t = tree())
		if (t->op != CON)
			error("Constant required");
	initflg--;
	return(t->value);
}
#
/* C compiler
 *
 *
 */

#include "c0h.c"

/*
 * Process a single external definition
 */
extdef()
{
	register o, elsize;
	int type, sclass;
	register struct hshtab *ds;

	if(((o=symbol())==EOF) || o==SEMI)
		return;
	peeksym = o;
	type = INT;
	sclass = EXTERN;
	xdflg = FNDEL;
	if ((elsize = getkeywords(&sclass, &type)) == -1 && peeksym!=NAME)
		goto syntax;
	if (type==STRUCT)
		blkhed();
	do {
		defsym = 0;
		decl1(EXTERN, type, 0, elsize);
		if ((ds=defsym)==0)
			return;
		funcsym = ds;
		ds->hflag =| FNDEL;
		outcode("BS", SYMDEF, ds->name);
		xdflg = 0;
		if ((ds->type&XTYPE)==FUNC) {
			if ((peeksym=symbol())==LBRACE || peeksym==KEYW) {
				funcblk.type = decref(ds->type);
				cfunc(ds->name);
				return;
			}
		} else 
			cinit(ds);
	} while ((o=symbol())==COMMA);
	if (o==SEMI)
		return;
syntax:
	if (o==RBRACE) {
		error("Too many }'s");
		peeksym = 0;
		return;
	}
	error("External definition syntax");
	errflush(o);
	statement(0);
}

/*
 * Process a function definition.
 */
cfunc(cs)
char *cs;
{
	register savdimp;

	savdimp = dimp;
	outcode("BBS", PROG, RLABEL, cs);
	declist(ARG);
	regvar = 5;
	retlab = isn++;
	if ((peeksym = symbol()) != LBRACE)
		error("Compound statement required");
	statement(1);
	outcode("BNB", LABEL, retlab, RETRN);
	dimp = savdimp;
}

/*
 * Process the initializers for an external definition.
 */
cinit(ds)
struct hshtab *ds;
{
	register basetype, nel, ninit;
	int o, width, realwidth;

	nel = 1;
	basetype = ds->type;
	/*
	 * If it's an array, find the number of elements.
	 * "basetype" is the type of thing it's an array of.
	 */
	while ((basetype&XTYPE)==ARRAY) {
		if ((nel = dimtab[ds->ssp&0377])==0)
			nel = 1;
		basetype = decref(basetype);
	}
	realwidth = width = length(ds) / nel;
	/*
	 * Pretend a structure is kind of an array of integers.
	 * This is a kludge.
	 */
	if (basetype==STRUCT) {
		nel =* realwidth/2;
		width = 2;
	}
	if ((peeksym=symbol())==COMMA || peeksym==SEMI) {
		outcode("BSN",CSPACE,ds->name,(nel*width+ALIGN)&~ALIGN);
		return;
	}
	ninit = 0;
	outcode("BBS", DATA, NLABEL, ds->name);
	if ((o=symbol())==LBRACE) {
		do
			ninit = cinit1(ds, basetype, width, ninit, nel);
		while ((o=symbol())==COMMA);
		if (o!=RBRACE)
			peeksym = o;
	} else {
		peeksym = o;
		ninit = cinit1(ds, basetype, width, 0, nel);
	}
	/*
	 * Above we pretended that a structure was a bunch of integers.
	 * Readjust in accordance with reality.
	 * First round up partial initializations.
	 */
	if (basetype==STRUCT) {
		if (o = 2*ninit % realwidth)
			outcode("BN", SSPACE, realwidth-o);
		ninit = (2*ninit+realwidth-2) / realwidth;
		nel =/ realwidth/2;
	}
	/*
	 * If there are too few initializers, allocate
	 * more storage.
	 * If there are too many initializers, extend
	 * the declared size for benefit of "sizeof"
	 */
	if (ninit<nel)
		outcode("BN", SSPACE, (nel-ninit)*realwidth);
	else if (ninit>nel) {
		if ((ds->type&XTYPE)==ARRAY)
			dimtab[ds->ssp&0377] = ninit;
		nel = ninit;
	}
	/*
	 * If it's not an array, only one initializer is allowed.
	 */
	if (ninit>1 && (ds->type&XTYPE)!=ARRAY)
		error("Too many initializers");
	if (((nel&width)&ALIGN))
		outcode("B", EVEN);
}

/*
 * Process a single expression in a sequence of initializers
 * for an external. Mainly, it's for checking
 * type compatibility.
 */
cinit1(ds, type, awidth, aninit, nel)
struct hshtab *ds;
{
	float sf;
	register struct tnode *s;
	register width, ninit;

	width = awidth;
	ninit = aninit;
	if ((peeksym=symbol())==STRING && type==CHAR) {
		peeksym = -1;
		if (ninit)
			bxdec();
		putstr(0);
		if (nel>nchstr) {
			strflg++;
			outcode("BN", SSPACE, nel-nchstr);
			strflg = 0;
			nchstr = nel;
		}
		return(nchstr);
	}
	if (peeksym==RBRACE)
		return(ninit);
	initflg++;
	s = tree();
	initflg = 0;
	switch(width) {

	case 1:
		if (s->op != CON)
			goto bad;
		outcode("B1N0", BDATA, s->value);
		break;

	case 2:
		if (s->op==CON) {
			outcode("B1N0", WDATA, s->value);
			break;
		}
		if (s->op==FCON || s->op==SFCON) {
			if (type==STRUCT) {
				ninit =+ 3;
				goto prflt;
			}
			goto bad;
		}
		rcexpr(block(1,INIT,0,0,s));
		break;

	case 4:
		sf = fcval;
		outcode("B1N1N0", WDATA, sf);
		goto flt;

	case 8:
	prflt:
		outcode("B1N1N1N1N0", WDATA, fcval);
	flt:
		if (s->op==FCON || s->op==SFCON)
			break;

	default:
	bad:
		bxdec();

	}
	return(++ninit);
}

bxdec()
{
	error("Inconsistent external initialization");
}

/*
 * Process one statement in a function.
 */
statement(d)
{
	register o, o1, o2;
	int o3, o4;
	struct tnode *np;

stmt:
	switch(o=symbol()) {

	case EOF:
		error("Unexpected EOF");
	case SEMI:
		return;

	case LBRACE:
		if (d) {
			if (proflg)
				outcode("BN", PROFIL, isn++);
			outcode("BN", SAVE, blkhed());
		}
		while (!eof) {
			if ((o=symbol())==RBRACE)
				return;
			peeksym = o;
			statement(0);
		}
		error("Missing '}'");
		return;

	case KEYW:
		switch(cval) {

		case GOTO:
			if (o1 = simplegoto())
				branch(o1);
			else 
				dogoto();
			goto semi;

		case RETURN:
			doret();
			goto semi;

		case IF:
			np = pexpr();
			o2 = 0;
			if ((o1=symbol())==KEYW) switch (cval) {
			case GOTO:
				if (o2=simplegoto())
					goto simpif;
				cbranch(np, o2=isn++, 0);
				dogoto();
				label(o2);
				goto hardif;

			case RETURN:
				if (nextchar()==';') {
					o2 = retlab;
					goto simpif;
				}
				cbranch(np, o1=isn++, 0);
				doret();
				label(o1);
				o2++;
				goto hardif;

			case BREAK:
				o2 = brklab;
				goto simpif;

			case CONTIN:
				o2 = contlab;
			simpif:
				chconbrk(o2);
				cbranch(np, o2, 1);
			hardif:
				if ((o=symbol())!=SEMI)
					goto syntax;
				if ((o1=symbol())==KEYW && cval==ELSE) 
					goto stmt;
				peeksym = o1;
				return;
			}
			peeksym = o1;
			cbranch(np, o1=isn++, 0);
			statement(0);
			if ((o=symbol())==KEYW && cval==ELSE) {
				o2 = isn++;
				branch(o2);
				label(o1);
				statement(0);
				label(o2);
				return;
			}
			peeksym = o;
			label(o1);
			return;

		case WHILE:
			o1 = contlab;
			o2 = brklab;
			label(contlab = isn++);
			cbranch(pexpr(), brklab=isn++, 0);
			statement(0);
			branch(contlab);
			label(brklab);
			contlab = o1;
			brklab = o2;
			return;

		case BREAK:
			chconbrk(brklab);
			branch(brklab);
			goto semi;

		case CONTIN:
			chconbrk(contlab);
			branch(contlab);
			goto semi;

		case DO:
			o1 = contlab;
			o2 = brklab;
			contlab = isn++;
			brklab = isn++;
			label(o3 = isn++);
			statement(0);
			label(contlab);
			contlab = o1;
			if ((o=symbol())==KEYW && cval==WHILE) {
				cbranch(tree(), o3, 1);
				label(brklab);
				brklab = o2;
				goto semi;
			}
			goto syntax;

		case CASE:
			o1 = conexp();
			if ((o=symbol())!=COLON)
				goto syntax;
			if (swp==0) {
				error("Case not in switch");
				goto stmt;
			}
			if(swp>=swtab+swsiz) {
				error("Switch table overflow");
			} else {
				swp->swlab = isn;
				(swp++)->swval = o1;
				label(isn++);
			}
			goto stmt;

		case SWITCH:
			o1 = brklab;
			brklab = isn++;
			np = pexpr();
			chkw(np, -1);
			rcexpr(block(1,RFORCE,0,0,np));
			pswitch();
			brklab = o1;
			return;

		case DEFAULT:
			if (swp==0)
				error("Default not in switch");
			if ((o=symbol())!=COLON)
				goto syntax;
			label(deflab = isn++);
			goto stmt;

		case FOR:
			o1 = contlab;
			o2 = brklab;
			contlab = isn++;
			brklab = isn++;
			if (o=forstmt())
				goto syntax;
			label(brklab);
			contlab = o1;
			brklab = o2;
			return;
		}

		error("Unknown keyword");
		goto syntax;

	case NAME:
		if (nextchar()==':') {
			peekc = 0;
			o1 = csym;
			if (o1->hclass>0) {
				error("Redefinition");
				goto stmt;
			}
			o1->hclass = STATIC;
			o1->htype = ARRAY;
			if (o1->hoffset==0)
				o1->hoffset = isn++;
			label(o1->hoffset);
			goto stmt;
		}
	}
	peeksym = o;
	rcexpr(tree());

semi:
	if ((o=symbol())==SEMI)
		return;
syntax:
	error("Statement syntax");
	errflush(o);
}

/*
 * Process a for statement.
 */
forstmt()
{
	register int l, o, sline;
	int sline1, *ss;
	struct tnode *st;

	if ((o=symbol()) != LPARN)
		return(o);
	if ((o=symbol()) != SEMI) {		/* init part */
		peeksym = o;
		rcexpr(tree());
		if ((o=symbol()) != SEMI)
			return(o);
	}
	label(contlab);
	if ((o=symbol()) != SEMI) {		/* test part */
		peeksym = o;
		rcexpr(block(1,CBRANCH,tree(),brklab,0));
		if ((o=symbol()) != SEMI)
			return(o);
	}
	if ((peeksym=symbol()) == RPARN) {	/* incr part */
		peeksym = -1;
		statement(0);
		branch(contlab);
		return(0);
	}
	l = contlab;
	contlab = isn++;
	st = tree();
	sline = line;
	if ((o=symbol()) != RPARN)
		return(o);
	ss = treespace;
	treespace = space;
	statement(0);
	sline1 = line;
	line = sline;
	label(contlab);
	rcexpr(st);
	line = sline1;
	treespace = ss;
	branch(l);
	return(0);
}

/*
 * A parenthesized expression,
 * as after "if".
 */
pexpr()
{
	register o, t;

	if ((o=symbol())!=LPARN)
		goto syntax;
	t = tree();
	if ((o=symbol())!=RPARN)
		goto syntax;
	return(t);
syntax:
	error("Statement syntax");
	errflush(o);
	return(0);
}

/*
 * The switch stateent, which involves collecting the
 * constants and labels for the cases.
 */
pswitch()
{
	register struct swtab *cswp, *sswp;
	int dl, swlab;

	cswp = sswp = swp;
	if (swp==0)
		cswp = swp = swtab;
	branch(swlab=isn++);
	dl = deflab;
	deflab = 0;
	statement(0);
	branch(brklab);
	label(swlab);
	if (deflab==0)
		deflab = brklab;
	outcode("BNN", SWIT, deflab, line);
	for (; cswp < swp; cswp++)
		outcode("NN", cswp->swlab, cswp->swval);
	outcode("0");
	label(brklab);
	deflab = dl;
	swp = sswp;
}

/*
 * blkhed is called at the start of each function.
 * It reads the declarations at the start;
 * then assigns storage locations for the
 * parameters (which have been linked into a list,
 * in order of appearance).
 * This list is necessary because in
 * f(a, b) float b; int a; ...
 * the names are seen before the types.
 * Also, the routine adjusts structures involved
 * in some kind of forward-referencing.
 */
blkhed()
{
	register pl;
	register struct hshtab *cs;

	autolen = 6;
	declist(0);
	pl = 4;
	while(paraml) {
		parame->hoffset = 0;
		cs = paraml;
		paraml = paraml->hoffset;
		if (cs->htype==FLOAT)
			cs->htype = DOUBLE;
		cs->hoffset = pl;
		cs->hclass = AUTO;
		if ((cs->htype&XTYPE) == ARRAY) {
			cs->htype =- (ARRAY-PTR);	/* set ptr */
			cs->ssp++;		/* pop dims */
		}
		pl =+ rlength(cs);
	}
	for (cs=hshtab; cs<hshtab+hshsiz; cs++) {
		if (cs->name[0] == '\0')
			continue;
		/* check tagged structure */
		if (cs->hclass>KEYWC && (cs->htype&TYPE)==RSTRUCT) {
			cs->lenp = dimtab[cs->lenp&0377]->lenp;
			cs->htype = cs->htype&~TYPE | STRUCT;
		}
		if (cs->hclass == STRTAG && dimtab[cs->lenp&0377]==0)
			error("Undefined structure: %.8s", cs->name);
		if (cs->hclass == ARG)
			error("Not an argument: %.8s", cs->name);
		if (stflg)
			prste(cs);
	}
	space = treespace;
	outcode("BN", SETREG, regvar);
	return(autolen);
}

/*
 * After a function definition, delete local
 * symbols.
 * Also complain about undefineds.
 */
blkend() {
	register struct hshtab *cs;

	for (cs=hshtab; cs<hshtab+hshsiz; cs++) {
		if (cs->name[0]) {
			if (cs->hclass==0 && (cs->hflag&FNUND)==0) {
				error("%.8s undefined", cs->name);
				cs->hflag =| FNUND;
			}
			if((cs->hflag&FNDEL)==0) {
				cs->name[0] = '\0';
				hshused--;
				cs->hflag =& ~(FNUND|FFIELD);
			}
		}
	}
}

/*
 * write out special definitions of local symbols for
 * benefit of the debugger.  None of these are used
 * by the assembler except to save them.
 */
prste(acs)
{
	register struct hshtab *cs;
	register nkind;

	cs = acs;
	switch (cs->hclass) {
	case REG:
		nkind = RNAME;
		break;

	case AUTO:
		nkind = ANAME;
		break;

	case STATIC:
		nkind = SNAME;
		break;

	default:
		return;

	}
	outcode("BSN", nkind, cs->name, cs->hoffset);
}

/*
 * In case of error, skip to the next
 * statement delimiter.
 */
errflush(ao)
{
	register o;

	o = ao;
	while(o>RBRACE)	/* ; { } */
		o = symbol();
	peeksym  = o;
}
#
/*
 * C compiler, phase 1
 *
 *
 * Handles processing of declarations,
 * except for top-level processing of
 * externals.
 */

#include "c0h.c"

/*
 * Process a sequence of declaration statements
 */
declist(sclass)
{
	register sc, elsize, offset;
	int type;

	offset = 0;
	sc = sclass;
	while ((elsize = getkeywords(&sclass, &type)) != -1) {
		offset = declare(sclass, type, offset, elsize);
		sclass = sc;
	}
	return(offset+align(INT, offset, 0));
}

/*
 * Read the keywords introducing a declaration statement
 */
getkeywords(scptr, tptr)
int *scptr, *tptr;
{
	register skw, tkw, longf;
	int o, elsize, isadecl, ismos;

	isadecl = 0;
	longf = 0;
	tkw = -1;
	skw = *scptr;
	elsize = 0;
	ismos = skw==MOS;
	for (;;) {
		mosflg = ismos;
		switch ((o=symbol())==KEYW? cval: -1) {

		case AUTO:
		case STATIC:
		case EXTERN:
		case REG:
			if (skw && skw!=cval)
				error("Conflict in storage class");
			skw = cval;
			break;
	
		case LONG:
			longf++;
			break;

		case STRUCT:
			o = STRUCT;
			elsize = strdec(&o, ismos);
			cval = o;
		case INT:
		case CHAR:
		case FLOAT:
		case DOUBLE:
			if (tkw>=0)
				error("Type clash");
			tkw = cval;
			break;
	
		default:
			peeksym = o;
			if (isadecl==0)
				return(-1);
			if (tkw<0)
				tkw = INT;
			if (skw==0)
				skw = AUTO;
			if (longf) {
				if (tkw==FLOAT)
					tkw = DOUBLE;
				else if (tkw==INT)
					tkw = LONG;
				else
					error("Misplaced 'long'");
			}
			*scptr = skw;
			*tptr = tkw;
			return(elsize);
		}
		isadecl++;
	}
}

/*
 * Process a structure declaration; a subroutine
 * of getkeywords.
 */
strdec(tkwp, mosf)
int *tkwp;
{
	register elsize, o;
	register struct hshtab *ssym;
	int savebits;
	struct hshtab *ds;

	mosflg = 1;
	ssym = 0;
	if ((o=symbol())==NAME) {
		ssym = csym;
		if (ssym->hclass==0) {
			ssym->hclass = STRTAG;
			ssym->lenp = dimp;
			chkdim();
			dimtab[dimp++] = 0;
		}
		if (ssym->hclass != STRTAG)
			redec();
		mosflg = mosf;
		o = symbol();
	}
	mosflg = 0;
	if (o != LBRACE) {
		if (ssym==0) {
		syntax:
			decsyn(o);
			return(0);
		}
		if (ssym->hclass!=STRTAG)
			error("Bad structure name");
		if ((elsize = dimtab[ssym->lenp&0377])==0) {
			*tkwp = RSTRUCT;
			elsize = ssym;
		}
		peeksym = o;
	} else {
		ds = defsym;
		mosflg = 0;
		savebits = bitoffs;
		bitoffs = 0;
		elsize = declist(MOS);
		bitoffs = savebits;
		defsym = ds;
		if ((o = symbol()) != RBRACE)
			goto syntax;
		if (ssym) {
			if (dimtab[ssym->lenp&0377])
				error("%.8s redeclared", ssym->name);
			dimtab[ssym->lenp&0377] = elsize;
		}
	}
	return(elsize);
}

/*
 * Check that the dimension table has not overflowed
 */
chkdim()
{
	if (dimp >= dimsiz) {
		error("Dimension/struct table overflow");
		exit(1);
	}
}

/*
 * Process a comma-separated list of declarators
 */
declare(askw, tkw, offset, elsize)
{
	register int o;
	register int skw;

	skw = askw;
	do {
		offset =+ decl1(skw, tkw, offset, elsize);
	} while ((o=symbol()) == COMMA);
	if (o==SEMI || o==RPARN && skw==ARG1)
		return(offset);
	decsyn(o);
}

/*
 * Process a single declarator
 */
decl1(askw, tkw, offset, elsize)
{
	int t1, chkoff, a;
	register int type, skw;
	register struct hshtab *dsym;

	skw = askw;
	chkoff = 0;
	mosflg = skw==MOS;
	if ((peeksym=symbol())==SEMI || peeksym==RPARN)
		return(0);
	/*
	 * Filler field
	 */
	if (peeksym==COLON && skw==MOS) {
		peeksym = -1;
		t1 = conexp();
		elsize = align(tkw, offset, t1);
		bitoffs =+ t1;
		return(elsize);
	}
	if ((t1=getype()) < 0)
		goto syntax;
	type = 0;
	do
		type = type<<TYLEN | (t1 & XTYPE);
	while (((t1=>>TYLEN) & XTYPE)!=0);
	type =| tkw;
	dsym = defsym;
	if (!(dsym->hclass==0
	   || (skw==ARG && dsym->hclass==ARG1)
	   || (skw==EXTERN && dsym->hclass==EXTERN && dsym->htype==type)))
		if (skw==MOS && dsym->hclass==MOS && dsym->htype==type)
			chkoff = 1;
		else {
			redec();
			goto syntax;
		}
	dsym->htype = type;
	if (skw)
		dsym->hclass = skw;
	if (skw==ARG1) {
		if (paraml==0)
			paraml = dsym;
		else
			parame->hoffset = dsym;
		parame = dsym;
	}
	if (elsize && ((type&TYPE)==RSTRUCT || (type&TYPE)==STRUCT)) {
		dsym->lenp = dimp;
		chkdim();
		dimtab[dimp++] = elsize;
	}
	elsize = 0;
	if (skw==MOS) {
		elsize = length(dsym);
		t1 = 0;
		if ((peeksym = symbol())==COLON) {
			elsize = 0;
			peeksym = -1;
			t1 = conexp();
			dsym->hflag =| FFIELD;
		}
		a = align(type, offset, t1);
		elsize =+ a;
		offset =+ a;
		if (t1) {
			if (chkoff && (dsym->bitoffs!=bitoffs
		 	 || dsym->flen!=t1))
				redec();
			dsym->bitoffs = bitoffs;
			dsym->flen = t1;
			bitoffs =+ t1;
		}
		if (chkoff && dsym->hoffset != offset)
			redec();
		dsym->hoffset = offset;
	}
	if ((dsym->htype&XTYPE)==FUNC) {
		if (dsym->hclass!=EXTERN && dsym->hclass!=AUTO)
			error("Bad function");
		dsym->hclass = EXTERN;
	}
	if (dsym->hclass==AUTO) {
		autolen =+ rlength(dsym);
		dsym->hoffset = -autolen;
	} else if (dsym->hclass==STATIC) {
		dsym->hoffset = isn;
		outcode("BBNBNB", BSS, LABEL, isn++,
		    SSPACE, rlength(dsym), PROG);
	} else if (dsym->hclass==REG) {
		if ((type&TYPE)>CHAR && (type&XTYPE)==0
		 || (type&XTYPE)>PTR || regvar<3)
			error("Bad register %o", type);
		dsym->hoffset = --regvar;
	}
syntax:
	return(elsize);
}

/*
 * Read a declarator and get the implied type
 */
getype()
{
	register int o, type;
	register struct hshtab *ds;

	switch(o=symbol()) {

	case TIMES:
		return(getype()<<TYLEN | PTR);

	case LPARN:
		type = getype();
		if ((o=symbol()) != RPARN)
			goto syntax;
		goto getf;

	case NAME:
		defsym = ds = csym;
		type = 0;
		ds->ssp = dimp;
	getf:
		switch(o=symbol()) {

		case LPARN:
			if (xdflg) {
				xdflg = 0;
				ds = defsym;
				declare(ARG1, 0, 0, 0);
				defsym = ds;
				xdflg++;
			} else
				if ((o=symbol()) != RPARN)
					goto syntax;
			type = type<<TYLEN | FUNC;
			goto getf;

		case LBRACK:
			chkdim();
			if ((o=symbol()) != RBRACK) {
				peeksym = o;
				cval = conexp();
				for (o=ds->ssp&0377; o<dimp; o++)
					dimtab[o] =* cval;
				dimtab[dimp++] = cval;
				if ((o=symbol())!=RBRACK)
					goto syntax;
			} else
				dimtab[dimp++] = 1;
			type = type<<TYLEN | ARRAY;
			goto getf;
		}
		peeksym = o;
		return(type);
	}
syntax:
	decsyn(o);
	return(-1);
}

/*
 * Enforce alignment restrictions in structures,
 * including bit-field considerations.
 */
align(type, offset, aflen)
{
	register a, t, flen;
	char *ftl;

	flen = aflen;
	a = offset;
	t = type;
	ftl = "Field too long";
	if (flen==0 && bitoffs) {
		a =+ (bitoffs-1) / NBPC;
		bitoffs = 0;
	}
	while ((t&XTYPE)==ARRAY)
		t = decref(t);
	if (t!=CHAR) {
		a = (a+ALIGN) & ~ALIGN;
		if (a>offset)
			bitoffs = 0;
	}
	if (flen) {
		if (type==INT) {
			if (flen > NBPW)
				error(ftl);
			if (flen+bitoffs > NBPW) {
				bitoffs = 0;
				a =+ NCPW;
			}
		} else if (type==CHAR) {
			if (flen > NBPC)
				error(ftl);
			if (flen+bitoffs > NCPW) {
				bitoffs = 0;
				a =+ 1;
			}
		} else
			error("Bad type for field");
	}
	return(a-offset);
}

/*
 * Complain about syntax error in declaration
 */
decsyn(o)
{
	error("Declaration syntax");
	errflush(o);
}

/*
 * Complain about a redeclaration
 */
redec()
{
	error("%.8s redeclared", defsym->name);
}
#
/*
 * C compiler
 *
 *
 */

#include "c0h.c"

/*
 * Reduce the degree-of-reference by one.
 * e.g. turn "ptr-to-int" into "int".
 */
decref(at)
{
	register t;

	t = at;
	if ((t & ~TYPE) == 0) {
		error("Illegal indirection");
		return(t);
	}
	return((t>>TYLEN) & ~TYPE | t&TYPE);
}

/*
 * Increase the degree of reference by
 * one; e.g. turn "int" to "ptr-to-int".
 */
incref(t)
{
	return(((t&~TYPE)<<TYLEN) | (t&TYPE) | PTR);
}

/*
 * Make a tree that causes a branch to lbl
 * if the tree's value is non-zero together with the cond.
 */
cbranch(tree, lbl, cond)
struct tnode *tree;
{
	rcexpr(block(1,CBRANCH,tree,lbl,cond));
}

/*
 * Write out a tree.
 */
rcexpr(tree)
struct tnode *tree;
{

	treeout(tree);
	outcode("BN", EXPR, line);
}

treeout(atree)
struct tnode *atree;
{
	register struct tnode *tree;

	if ((tree = atree) == 0)
		return;
	switch(tree->op) {

	case 0:
		outcode("B", NULL);
		return;

	case NAME:
		outcode("BNN", NAME, tree->class, tree->type);
		if (tree->class==EXTERN)
			outcode("S", tree->nname);
		else
			outcode("N", tree->nloc);
		return;

	case CON:
	case FCON:
	case SFCON:
		outcode("BNN", tree->op, tree->type, tree->value);
		return;

	case FSEL:
		treeout(tree->tr1);
		outcode("BNN", tree->op, tree->type, tree->tr2);
		return;

	case CBRANCH:
		treeout(tree->btree);
		outcode("BNN", tree->op, tree->lbl, tree->cond);
		return;

	default:
		treeout(tree->tr1);
		if (opdope[tree->op]&BINARY)
			treeout(tree->tr2);
		outcode("BN", tree->op, tree->type);
		return;
	}
}

/*
 * Generate a branch
 */
branch(lab) {
	outcode("BN", BRANCH, lab);
}

/*
 * Generate a label
 */
label(l) {
	outcode("BN", LABEL, l);
}

/*
 * ap is a tree node whose type
 * is some kind of pointer; return the size of the object
 * to which the pointer points.
 */
plength(ap)
struct tname *ap;
{
	register t, l;
	register struct tname *p;

	p = ap;
	if (p==0 || ((t=p->type)&~TYPE) == 0)		/* not a reference */
		return(1);
	p->type = decref(t);
	l = length(p);
	p->type = t;
	return(l);
}

/*
 * return the number of bytes in the object
 * whose tree node is acs.
 */
length(acs)
struct tnode *acs;
{
	register t, n;
	register struct tnode *cs;

	cs = acs;
	t = cs->type;
	n = 1;
	while ((t&XTYPE) == ARRAY) {
		t = decref(t);
		n = dimtab[cs->ssp&0377];
	}
	if ((t&~TYPE)==FUNC)
		return(0);
	if (t>=PTR)
		return(2*n);
	switch(t&TYPE) {

	case INT:
		return(2*n);

	case CHAR:
		return(n);

	case FLOAT:
	case LONG:
		return(4*n);

	case DOUBLE:
		return(8*n);

	case STRUCT:
		return(n * dimtab[cs->lenp&0377]);

	case RSTRUCT:
		error("Bad structure");
		return(0);
	}
	error("Compiler error (length)");
}

/*
 * The number of bytes in an object, rounded up to a word.
 */
rlength(cs)
struct tnode *cs;
{
	return((length(cs)+ALIGN) & ~ALIGN);
}

/*
 * After an "if (...) goto", look to see if the transfer
 * is to a simple label.
 */
simplegoto()
{
	register struct hshtab *csp;

	if ((peeksym=symbol())==NAME && nextchar()==';') {
		csp = csym;
		if (csp->hclass==0 && csp->htype==0) {
			csp->htype = ARRAY;
			if (csp->hoffset==0)
				csp->hoffset = isn++;
		}
		if ((csp->hclass==0||csp->hclass==STATIC)
		 &&  csp->htype==ARRAY) {
			peeksym = -1;
			return(csp->hoffset);
		}
	}
	return(0);
}

/*
 * Return the next non-white-space character
 */
nextchar()
{
	while (spnextchar()==' ')
		peekc = 0;
	return(peekc);
}

/*
 * Return the next character, translating all white space
 * to blank and handling line-ends.
 */
spnextchar()
{
	register c;

	if ((c = peekc)==0)
		c = getchar();
	if (c=='\t')
		c = ' ';
	else if (c=='\n') {
		c = ' ';
		if (inhdr==0)
			line++;
		inhdr = 0;
	} else if (c=='\001') {	/* SOH, insert marker */
		inhdr++;
		c = ' ';
	}
	peekc = c;
	return(c);
}

/*
 * is a break or continue legal?
 */
chconbrk(l)
{
	if (l==0)
		error("Break/continue error");
}

/*
 * The goto statement.
 */
dogoto()
{
	register struct tnode *np;

	*cp++ = tree();
	build(STAR);
	chkw(np = *--cp, -1);
	rcexpr(block(1,JUMP,0,0,np));
}

/*
 * The return statement, which has to convert
 * the returned object to the function's type.
 */
doret()
{
	register struct tnode *t;

	if (nextchar() != ';') {
		t = tree();
		*cp++ = &funcblk;
		*cp++ = t;
		build(ASSIGN);
		cp[-1] = cp[-1]->tr2;
		build(RFORCE);
		rcexpr(*--cp);
	}
	branch(retlab);
}

/*
 * write out a character to the usual output
 * or to the string file
 */
putchar(c)
{
	write(1, &c, 1);
}

outcode(s, a)
char *s;
{
	register char *sp;
	register *ap, *bufp;
	int n;
	char *np;

	bufp = obuf;
	if (strflg)
		bufp = sbuf;
	ap = &a;
	for (;;) switch(*s++) {
	case 'B':
		putw(*ap++ | (0376<<8), bufp);
		continue;

	case 'N':
		putw(*ap++, bufp);
		continue;

	case 'S':
		np = *ap++;
		n = ncps;
		while (n-- && *np) {
			putc(*np++, bufp);
		}
		putc(0, bufp);
		continue;

	case '1':
		putw(1, bufp);
		continue;

	case '0':
		putw(0, bufp);
		continue;

	case '\0':
		return;
	}
	error("Botch in outcode");
}
#
#include "c0h.c"
/*
 *  info on operators:
 *   01-- is binary operator
 *   02-- left (or only) operand must be lvalue
 *   04-- is relational operator
 *  010-- is assignment-type operator
 *  020-- non-float req. on left
 *  040-- non-float req. on right
 * 0100-- is commutative
 * 0200-- is right, not left-associative
 * 0400-- is leaf of tree
 * *0XX000-- XX is priority of operator
 */
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
	000000,	/* 27 */
	000000,	/* 28 */
	000000, /* 29 */
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
	017161,	/* | */
	017161,	/* ^ */
	036001,	/* -> */
	000000, /* int -> double */
	000000, /* double -> int */
	016001, /* && */
	015001, /* || */
	030001, /* &~ */
	000000, /* 56 */
	000000, /* 57 */
	000000, /* 58 */
	000000,	/* 59 */
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
	000000,	/* 81 */
	000000,	/* 82 */
	000000,	/* 83 */
	000000,	/* 84 */
	000000,	/* 85 */
	000000,	/* 86 */
	000000,	/* 87 */
	000000,	/* 88 */
	000000,	/* 89 */
	014201,	/* ? */
	034200,	/* sizeof */
	000000,	/* 92 */
	000000,	/* 93 */
	000000,	/* 94 */
	000000,	/* 95 */
	000000,	/* 96 */
	000000,	/* 97 */
	000000,	/* 98 */
	000000,	/* 99 */
	036001,	/* call */
	036001,	/* mcall */
	000000,	/* goto */
	000000,	/* jump cond */
	000000,	/* branch cond */
	000000,	/* 105 */
	000000, /* 106 */
	000000,	/* 107 */
	000000,	/* 108 */
	000000,	/* 109 */
	000000	/* force r0 */
};

/*
 * conversion table:
 * FTI: float (or double) to integer
 * ITF: integer to float
 * ITP: integer to pointer
 * ITL: integer to long
 * LTI: long to integer
 * LTF: long to float
 * FTL: float to long
 * PTI: pointer to integer
 * XX: usually illegal
 * When FTI, LTI, FTL are added in they specify
 * that it is the left operand that should be converted.
 * For + this is done and the conversion is turned back into
 * ITF, ITL, LTF.
 * For = however the left operand can't be converted
 * and the specified conversion is applied to the rhs.
 */
char cvtab[4][4] {
/*		int	double		long		ptr */
/* int */	0,	(FTI<<4)+ITF,	(LTI<<4)+ITL,	(ITP<<4)+ITP,	
/* double */	ITF,	0,		LTF,		XX,
/* long */	ITL,	(FTL<<4)+LTF,	0,		XX,
/* ptr */	ITP,	XX,		XX,		PTI
};

/*
 * character type table
 */
char ctab[] {
	EOF,	INSERT,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,
	UNKN,	SPACE,	NEWLN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,
	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,
	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,	UNKN,
	SPACE,	EXCLA,	DQUOTE,	UNKN,	UNKN,	MOD,	 AND,	SQUOTE,
	LPARN,	RPARN,	TIMES,	PLUS,	COMMA,	MINUS,	PERIOD,	DIVIDE,
	DIGIT,	DIGIT,	DIGIT,	DIGIT,	DIGIT,	DIGIT,	DIGIT,	DIGIT,
	DIGIT,	DIGIT,	COLON,	SEMI,	LESS,	ASSIGN,	GREAT,	QUEST,
	UNKN,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LBRACK,	UNKN,	RBRACK,	EXOR,	LETTER,
	UNKN,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,	LETTER,
	LETTER,	LETTER,	LETTER,	LBRACE,	OR,	RBRACE,	COMPL,	UNKN
};
