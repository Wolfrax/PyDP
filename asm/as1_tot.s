/
/

/ PDP-11 assembler pass 0

indir	= 0

	jmp	start
go:
	jsr	pc,assem
	movb	pof,r0
	sys	write; outbuf; 512.
	movb	pof,r0
	sys	close
	movb	fbfil,r0
	sys	close
	tstb	errflg
	bne	aexit
	jsr	r5,fcreat; a.tmp3
	mov	r0,r1
	mov	symend,0f
	sub	$usymtab,0f
	sys	indir; 9f
	.data
9:	sys	write; usymtab; 0:..
	.text
	mov	r1,r0
	sys	close
	sys	exec; 2f; 1f
	mov	$2f,r0
	jsr	r5,filerr; "?\n

aexit:
	sys	unlink; a.tmp1
	sys	unlink; a.tmp2
	sys	unlink; a.tmp3
	sys	exit
.data
1:
	2f
	a.tmp1
	a.tmp2
	a.tmp3
unglob:
	3f
	0
	.text
2:
fpass2:
	</lib/as2\0>
3:
	<-g\0>
	.even

filerr:
	mov	r4,-(sp)            / push r4 to stack
	mov	r0,r4               / move r0 -> r4, r0 have address to filename-string
	mov	r4,0f               / move r4 -> label 0 (sys write below)
	clr	r0                  / clear r0
1:
	tstb	(r4)+           / set Z-bit to 1 if (r4) is 0, set N-bit to 1 if (r4) is < 0, increment r4
	beq	1f                  / branch if Z-bit is zero
	inc	r0                  / increment r0 with 1, counter for number of characters
	br	1b                  / branch backward to label 1
1:
	mov	r0,1f               / move r0 (number of characters) to label 1 (forward)
	mov	$1,r0               / move $1 -> r0
	sys	indir; 9f           / make an indirect system call at label 9
	.data
9:	sys	write; 0:0; 1:0     / write to file descriptor in r0 (1 - stdout), from buffer in label 0 (filename), number of bytes in label 1
	.text
	mov	r5,0f               / r5 is pointing to next instruction after jsr ("?\n"), move to label 0
	mov	$1,r0               / move $1 -> r0
	sys	indir; 9f           / make an indirect system call at label 9
	.data
9:	sys	write; 0:0; 2       / write for file descriptor in r0 (1 - stdout), from buffer in label 0 ("?\n"), 2 character (\tmp\atm1a?\n)
	.text
	tst	(r5)+               / test r5 ("?\n"), incr r5 (point to instr following ("?\n")". Clear all status bits
	mov	(sp)+,r4            / pop saved value back to r4
	rts	r5                  / return and execute from next statement

fcreat:
	mov	r4,-(sp)              / move r4 -> sp address - 1
	mov	(r5)+,r4              / move value pointed from r5 (pointer to a.tmp* string) to r4, increment r5 (next statement)
	mov	r4,0f                 / move r4 -> label 0 (sys stat below: ..)
1:
	sys	indir; 9f             / make an indirect system call at label 9
	.data
9:	sys	stat; 0:..; outbuf    / get file status, store in outbuf (as18.s: .=.+512.)
	.text
	bec	2f                    / (bcc) branch forward if carry (error/C-bit) is clear (no error) to label 2
	mov	r4,0f                 / mov r4 -> label 0 (sys creat below: ..)
	sys	indir; 9f             / make an indirect system call at label 9
	.data
9:	sys	creat; 0:..; 444      / create file, name at address at r4 (r4 moved to label 0), mode 444 (read only), file descr in r0
	.text
	bes	2f                    / (bcs) branch forward to 2 if carry (error/c-bit) is set, file not created
	mov	(sp)+,r4              / move referenced value at stack -> r4, increment sp
	rts	r5                    / set pc <- r5, pop what is on stack and -> r5
2:
	incb	9.(r4)            / increment with 1 value (byte) at address r4 + 9, eg r4 -> "/tmp/atm1a" to "/tmp/atm1b"
	cmpb	9.(r4),$'z        / compare (byte)  value (byte) at address r4 + 9 with $'z
	blos	1b                / branch, if lower or same, backwards to 1, try with new file name
	mov	r4,r0                 / r4 -> r0, r4 is address pointer to filename-string
	jsr	r5,filerr; "?\n       / jump to filerr
	sys	exit                  / exit program
/
/

/ a2 -- pdp-11 assembler pass 1

error:
	incb	errflg
	mov	r0,-(sp)
	mov	r1,-(sp)
	mov	(r5)+,r0
	tst	*curarg
	beq	1f
	mov	r0,-(sp)
	mov	*curarg,r0
	clr	*curarg
	jsr	r5,filerr; '\n
	mov	(sp)+,r0
1:
	mov	r2,-(sp)
	mov	r3,-(sp)
	mov	line,r3
	movb	r0,1f
	mov	$1f+6,r0
	mov	$4,r1
2:
	clr	r2
	dvd	$10.,r2
	add	$'0,r3
	movb	r3,-(r0)
	mov	r2,r3
	sob	r1,2b
	mov	$1,r0
	sys	write; 1f; 7
	mov	(sp)+,r3
	mov	(sp)+,r2
	mov	(sp)+,r1
	mov	(sp)+,r0
	rts	r5

	.data
1:	<f xxxx\n>
	.even
	.text

betwen:
	cmp	r0,(r5)+
	blt	1f
	cmp	(r5)+,r0
	blt	2f
1:
	tst	(r5)+
2:
	rts	r5

putw:
	tst	ifflg
	beq	1f
	cmp	r4,$'\n
	bne	2f
1:
	mov	r4,*obufp
	add	$2,obufp
	cmp	obufp,$outbuf+512.
	blo	2f
	mov	$outbuf,obufp
	movb	pof,r0
	sys	write; outbuf; 512.
2:
	rts	pc

/
/

/ a3 -- pdp-11 assembler pass 1

assem:
	jsr	pc,readop
	jsr	pc,checkeos
		br ealoop
	tst	ifflg
	beq	3f
	cmp	r4,$200
	blos	assem
	cmpb	(r4),$21	/if
	bne	2f
	inc	ifflg
2:
	cmpb	(r4),$22   /endif
	bne	assem
	dec	ifflg
	br	assem
3:
	mov	r4,-(sp)
	jsr	pc,readop
	cmp	r4,$'=
	beq	4f
	cmp	r4,$':
	beq	1f
	mov	r4,savop
	mov	(sp)+,r4
	jsr	pc,opline
	br	ealoop
1:
	mov	(sp)+,r4
	cmp	r4,$200
	bhis	1f
	cmp	r4,$1		/ digit
	beq	3f
	jsr	r5,error; 'x
	br	assem
1:
	bitb	$37,(r4)
	beq	1f
	jsr	r5,error; 'm
1:
	bisb	dot-2,(r4)
	mov	dot,2(r4)
	br	assem
3:
	mov	numval,r0
	jsr	pc,fbcheck
	movb	dotrel,curfbr(r0)
	asl	r0
	movb	dotrel,nxtfb
	mov	dot,nxtfb+2
	movb	r0,nxtfb+1
	mov	dot,curfb(r0)
	movb	fbfil,r0
	sys	write; nxtfb; 4
	br	assem
4:
	jsr	pc,readop
	jsr	pc,expres
	mov	(sp)+,r1
	cmp	r1,$200
	bhis	1f
	jsr	r5,error; 'x
	br	ealoop
1:
	cmp	r1,$dotrel
	bne	2f
	bic	$40,r3
	cmp	r3,dotrel
	bne	1f
2:
	bicb	$37,(r1)
	bic	$!37,r3
	bne	2f
	clr	r2
2:
	bisb	r3,(r1)
	mov	r2,2(r1)
	br	ealoop
1:
	jsr	r5,error; '.
	movb	$2,dotrel
ealoop:
	cmp	r4,$';
	beq	assem1
	cmp	r4,$'\n
	bne	1f
	inc	line
	br	assem1
1:
	cmp	r4,$'\e
	bne	2f
	tst	ifflg
	beq	1f
	jsr	r5,error; 'x
1:
	rts	pc
2:
	jsr	r5,error; 'x
2:
	jsr	pc,checkeos
		br assem1
	jsr	pc,readop
	br	2b
assem1:
	jmp	assem

fbcheck:
	cmp	r0,$9.
	bhi	1f
	rts	pc
1:
	jsr	r5,error; 'f
	clr	r0
	rts	pc

checkeos:
	cmp	r4,$'\n
	beq	1f
	cmp	r4,$';
	beq	1f
	cmp	r4,$'\e
	beq	1f
	add	$2,(sp)
1:
	rts	pc

/
/

/ a4 -- pdp-11 assembler pass1

rname:
	mov	r1,-(sp)
	mov	r2,-(sp)
	mov	r3,-(sp)
	mov	$8,r5
	mov	$symbol+8.,r2
	clr	-(r2)
	clr	-(r2)
	clr	-(r2)
	clr	-(r2)
	clr	-(sp)
	clr	-(sp)
	cmp	r0,$'~		/  symbol not for hash table
	bne	1f
	inc	2(sp)
	clr	ch
1:
	jsr	pc,rch
	movb	chartab(r0),r3
	ble	1f
	add	r3,(sp)
	swab	(sp)
	dec	r5
	blt	1b
	movb	r3,(r2)+
	br	1b
1:
	mov	r0,ch
	mov	(sp)+,r1
	clr	r0
	tst	(sp)+
	beq	1f
	mov	symend,r4
	br	4f
1:
	div	$hshsiz,r0
	ashc	$1,r0
	add	$hshtab,r1
1:
	sub	r0,r1
	cmp	r1,$hshtab
	bhi	2f
	add	$2*hshsiz,r1
2:
	mov	$symbol,r2
	mov	-(r1),r4
	beq	3f
	cmp	(r2)+,(r4)+
	bne	1b
	cmp	(r2)+,(r4)+
	bne	1b
	cmp	(r2)+,(r4)+
	bne	1b
	cmp	(r2)+,(r4)+
	bne	1b
	br	1f
3:
	mov	symend,r4
	mov	r4,(r1)
4:
	mov	$symbol,r2
	mov	r4,-(sp)
	add	$20,r4
	cmp	r4,0f
	blos	4f
	add	$512.,0f
	sys	indir; 9f
	.data
9:	sys	break; 0:end
	.text
4:
	mov	(sp)+,r4
	mov	(r2)+,(r4)+
	mov	(r2)+,(r4)+
	mov	(r2)+,(r4)+
	mov	(r2)+,(r4)+
	clr	(r4)+
	clr	(r4)+
	mov	r4,symend
	sub	$4,r4
1:
	mov	r4,-(sp)
	mov	r4,r3
	sub	$8,r3
	cmp	r3,$usymtab
	blo	1f
	sub	$usymtab,r3
	clr	r2
	div	$3,r2
	mov	r2,r4
	add	$4000,r4		/ user symbol
	br	2f
1:
	sub	$symtab,r3
	clr	r2
	div	$3,r2
	mov	r2,r4
	add	$1000,r4		/ builtin symbol
2:
	jsr	pc,putw
	mov	(sp)+,r4
	mov	(sp)+,r3
	mov	(sp)+,r2
	mov	(sp)+,r1
	tst	(sp)+
	rts	pc

number:
	mov	r2,-(sp)
	mov	r3,-(sp)
	mov	r5,-(sp)
	clr	r1
	clr	r5
1:
	jsr	pc,rch
	jsr	r5,betwen; '0; '9
		br 1f
	sub	$'0,r0
	mpy	$10.,r5
	add	r0,r5
	als	$3,r1
	add	r0,r1
	br	1b
1:
	cmp	r0,$'b
	beq	1f
	cmp	r0,$'f
	beq	1f
	cmp	r0,$'.
	bne	2f
	mov	r5,r1
	clr	r0
2:
	movb	r0,ch
	mov	r1,r0
	mov	(sp)+,r5
	mov	(sp)+,r3
	mov	(sp)+,r2
	rts	pc
1:
	mov	r0,r3
	mov	r5,r0
	jsr	pc,fbcheck
	add	$141,r0
	cmp	r3,$'b
	beq	1f
	add	$10.,r0
1:
	mov	r0,r4
	mov	(sp)+,r5
	mov	(sp)+,r3
	mov	(sp)+,r2
	add	$2,(sp)
	rts	pc

rch:
	movb	ch,r0
	beq	1f
	clrb	ch
	rts	pc
1:
	dec	inbfcnt
	blt	2f
	movb	*inbfp,r0
	inc	inbfp
	bic	$!177,r0
	beq	1b
	rts	pc
2:
	movb	fin,r0
	beq	3f
	sys	read; inbuf;512.
	bcs	2f
	tst	r0
	beq	2f
	mov	r0,inbfcnt
	mov	$inbuf,inbfp
	br	1b
2:
	movb	fin,r0
	clrb	fin
	sys	close
3:
	decb	nargs
	bgt	2f
	mov	$'\e,r0
	rts	pc
2:
	tst	ifflg
	beq	2f
	jsr	r5,error; 'i
	jmp	aexit
2:
	mov	curarg,r0
	tst	(r0)+
	mov	(r0),0f
	mov	r0,curarg
	incb	fileflg
	sys	indir; 9f
	.data
9:	sys	open; 0:0; 0
	.text
	bec	2f
	mov	0b,r0
	jsr	r5,filerr; <?\n>
	jmp	 aexit
2:
	movb	r0,fin
	mov	$1,line
	mov	r4,-(sp)
	mov	r1,-(sp)
	mov	$5,r4
	jsr	pc,putw
	mov	*curarg,r1
2:
	movb	(r1)+,r4
	beq	2f
	jsr	pc,putw
	br	2b
2:
	mov	$-1,r4
	jsr	pc,putw
	mov	(sp)+,r1
	mov	(sp)+,r4
	br	1b

/
/

/ a5 -- pdp-11 assembler pass 1

readop:
	mov	savop,r4
	beq	1f
	clr	savop
	rts	pc
1:
	jsr	pc,8f
	jsr	pc,putw
	rts	pc

8:
	jsr	pc,rch
_readop:
	mov	r0,r4
	movb	chartab(r0),r1
	bgt	rdname
	jmp	*1f-2(r1)

	fixor
	escp
	8b
	retread
	dquote
	garb
	squote
	rdname
	skip
	rdnum
	retread
	string
1:

escp:
	jsr	pc,rch
	mov	$esctab,r1
1:
	cmpb	r0,(r1)+
	beq	1f
	tstb	(r1)+
	bne	1b
	rts	pc
1:
	movb	(r1),r4
	rts	pc

esctab:
	.byte '/, '/
	.byte '\<, 035
	.byte '>, 036
	.byte '%, 037
	.byte 0, 0

fixor:
	mov	$037,r4
retread:
	rts	pc

rdname:
	movb	r0,ch
	cmp	r1,$'0
	blo	1f
	cmp	r1,$'9
	blos	rdnum
1:
	jmp	rname

rdnum:
	jsr	pc,number
		br 1f
	rts	pc

squote:
	jsr	pc,rsch
	br	1f
dquote:
	jsr	pc,rsch
	mov	r0,-(sp)
	jsr	pc,rsch
	swab	r0
	bis	(sp)+,r0
1:
	mov	r0,numval
	mov	$1,r4
	jsr	pc,putw
	mov	numval,r4
	jsr	pc,putw
	mov	$1,r4
	tst	(sp)+
	rts	pc

skip:
	jsr	pc,rch
	mov	r0,r4
	cmp	r0,$'\e
	beq	1f
	cmp	r0,$'\n
	bne	skip
1:
	rts	pc

garb:
	jsr	r5,error; 'g
	br	8b

string:
	mov	$'<,r4
	jsr	pc,putw
	clr	numval
1:
	jsr	pc,rsch
	tst	r1
	bne	1f
	mov	r0,r4
	bis	$400,r4
	jsr	pc,putw
	inc	 numval
	br	1b
1:
	mov	$-1,r4
	jsr	pc,putw
	mov	$'<,r4
	tst	(sp)+
	rts	pc

rsch:
	jsr	pc,rch
	cmp	r0,$'\e
	beq	4f
	cmp	r0,$'\n
	beq	4f
	clr	r1
	cmp	r0,$'\\
	bne	3f
	jsr	pc,rch
	mov	$schar,r2
1:
	cmpb	(r2)+,r0
	beq	2f
	tstb	(r2)+
	bpl	1b
	rts	pc
2:
	movb	(r2)+,r0
	clr	r1
	rts	pc
3:
	cmp	r0,$'>
	bne	1f
	inc	r1
1:
	rts	pc
4:
	jsr	r5,error; '<
	jmp	aexit

schar:
	.byte 'n, 012
	.byte 't, 011
	.byte 'e, 004
	.byte '0, 000
	.byte 'r, 015
	.byte 'a, 006
	.byte 'p, 033
	.byte 0,  -1

/
/

/ a6 -- pdp-11 assembler pass 1

opline:
	mov	r4,r0
	jsr	r5,betwen; 0; 200
		br	1f
	cmp	r0,$'<
	bne	xpr
	jmp	opl17
xpr:
	jsr	pc,expres
	add	$2,dot
	rts	pc
1:
	movb	(r4),r0
	cmp	r0,$24
	beq	xpr
	jsr	r5,betwen; 5; 36
		br xpr
	mov	r0,-(sp)
	jsr	pc,readop
	mov	(sp)+,r0
	asl	r0
	jmp	*1f-12(r0)

1:
	opl13	/ map fop freg,fdst to double
	opl6
	opl7
	opl10
	opl11
	opl13	/ map fld/fst to double
	opl13
	opl13	/ map fop fsrc,freg to double
	opl15
	opl16
	opl17
	opl20
	opl21
	opl22
	opl23
	xpr
	opl25
	opl26
	opl27
	opl13  / map mul s,r to double
	opl31
	opl32
	xpr
	xpr
	opl35
	opl36

/ jbr
opl35:
	mov	$4,-(sp)
	br	1f

/ jeq, etc
opl36:
	mov	$6,-(sp)
1:
	jsr	pc,expres
	cmp	r3,dotrel
	bne	1f
	sub	dot,r2
	bge	1f
	cmp	r2,$-376
	blt	1f
	mov	$2,(sp)
1:
	add	(sp)+,dot
	rts	pc

/double
opl13:
opl7:
	jsr	pc,addres
op2:
	cmp	r4,$',
	beq	1f
	jsr	pc,errora
	rts	pc
1:
	jsr	pc,readop
opl15:   / single operand
	jsr	pc,addres
	add	$2,dot
	rts	pc

opl31:	/ sob
	jsr	pc,expres
	cmp	r4,$',
	beq	1f
	jsr	pc,errora
1:
	jsr	pc,readop

/branch
opl6:
opl10:
opl11:
	jsr	pc,expres
	add	$2,dot
	rts	pc

/ .byte
opl16:
	jsr	pc,expres
	inc	dot
	cmp	r4,$',
	bne	1f
	jsr	pc,readop
	br	opl16
1:
	rts	pc

/ < (.ascii)
opl17:
	add	numval,dot
	jsr	pc,readop
	rts	pc

/.even
opl20:
	inc	dot
	bic	$1,dot
	rts	pc

/.if
opl21:
	jsr	pc,expres
	tst	r3
	bne	1f
	jsr	r5,error; 'U
1:
	tst	r2
	bne	opl22
	inc	ifflg
opl22:	/endif
	rts	pc

/.globl
opl23:
	cmp	r4,$200
	blo	1f
	bisb	$40,(r4)
	jsr	pc,readop
	cmp	r4,$',
	bne	1f
	jsr	pc,readop
	br	opl23
1:
	rts	pc

opl25:
opl26:
opl27:
	mov	dotrel,r1
	asl	r1
	mov	dot,savdot-4(r1)
	mov	savdot-[2*25](r0),dot
	asr	r0
	sub	$25-2,r0
	mov	r0,dotrel
	rts	pc

/ .common
opl32:
	cmp	r4,$200
	blo	1f
	bis	$40,(r4)
	jsr	pc,readop
	cmp	r4,$',
	bne	1f
	jsr	pc,readop
	jsr	pc,expres
	rts	pc
1:
	jsr	r5,error; 'x
	rts	pc

addres:
	cmp	r4,$'(
	beq	alp
	cmp	r4,$'-
	beq	amin
	cmp	r4,$'$
	beq	adoll
	cmp	r4,$'*
	beq	astar
getx:
	jsr	pc,expres
	cmp	r4,$'(
	bne	2f
	jsr	pc,readop
	jsr	pc,expres
	jsr	pc,checkreg
	jsr	pc,checkrp
	add	$2,dot
	clr	r0
	rts	pc
2:
	cmp	r3,$24		/ register type
	bne	1f
	jsr	pc,checkreg
	clr	r0
	rts	pc
1:
	add	$2,dot
	clr	r0
	rts	pc

alp:
	jsr	pc,readop
	jsr	pc,expres
	jsr	pc,checkrp
	jsr	pc,checkreg
	cmp	r4,$'+
	bne	1f
	jsr	pc,readop
	clr	r0
	rts	pc
1:
	mov	$2,r0
	rts	pc

amin:
	jsr	pc,readop
	cmp	r4,$'(
	beq	1f
	mov	r4,savop
	mov	$'-,r4
	br	getx
1:
	jsr	pc,readop
	jsr	pc,expres
	jsr	pc,checkrp
	jsr	pc,checkreg
	clr	r0
	rts	pc

adoll:
	jsr	pc,readop
	jsr	pc,expres
	add	$2,dot
	clr	r0
	rts	pc

astar:
	jsr	pc,readop
	cmp	r4,$'*
	bne	1f
	jsr	r5,error; '*
1:
	jsr	pc,addres
	add	r0,dot
	rts	pc

errora:
	jsr	r5,error; 'a
	rts	pc

checkreg:
	cmp	r2,$7
	bhi	1f
	cmp	r3,$1
	beq	2f
	cmp	r3,$4
	bhi	2f
1:
	jsr	pc,errora
2:
	rts	pc

errore:
	jsr	r5,error; 'e
	rts	pc

checkrp:
	cmp	r4,$')
	beq	1f
	jsr	r5,error; ')
	rts	pc
1:
	jsr	pc,readop
	rts	pc

/
/

/  a7 -- pdp-11 assembler pass 1

expres:
	mov	r5,-(sp)
	mov	$'+,-(sp)
	clr	opfound
	clr	r2
	mov	$1,r3
	br	1f
advanc:
	jsr	pc,readop
1:
	mov	r4,r0
	jsr	r5,betwen; 0; 177
		br .+4
	br	7f
	movb	(r4),r0
	mov	2(r4),r1
	br	oprand
7:
	cmp	r4,$141
	blo	1f
	cmp	r4,$141+10.
	bhis	2f
	movb	curfbr-141(r4),r0
	asl	r4
	mov	curfb-2*141](r4),r2
	bpl	oprand
	jsr	r5,error; 'f
	br	oprand
2:
	clr	r3
	clr	r2
	br	oprand
1:
	mov	$esw1,r1
1:
	cmp	(r1)+,r4
	beq	1f
	tst	(r1)+
	bne	1b
	tst	opfound
	bne	2f
	jsr	pc,errore
2:
	tst	(sp)+
	mov	(sp)+,r5
	rts	pc
1:
	jmp	*(r1)

esw1:
	'+;	binop
	'-;	binop
	'*;	binop
	'/;	binop
	'&;	binop
	037;	binop
	035;	binop
	036;	binop
	'%;	binop
	'[;	brack
	'^;	binop
	1;	exnum
	'!;	binop
	0;	0

binop:
	cmpb	(sp),$'+
	beq	1f
	jsr	pc,errore
1:
	movb	r4,(sp)
	br	advanc

exnum:
	mov	numval,r1
	mov	$1,r0
	br	oprand

brack:
	mov	r2,-(sp)
	mov	r3,-(sp)
	jsr	pc,readop
	jsr	pc,expres
	cmp	r4,$']
	beq	1f
	jsr	r5,error; ']
1:
	mov	r3,r0
	mov	r2,r1
	mov	(sp)+,r3
	mov	(sp)+,r2

oprand:
	inc	opfound
	mov	$exsw2,r5
1:
	cmp	(sp),(r5)+
	beq	1f
	tst	(r5)+
	bne	1b
	br	eoprnd
1:
	jmp	*(r5)

exsw2:
	'+; exadd
	'-; exsub
	'*; exmul
	'/; exdiv
	037; exor
	'&; exand
	035;exlsh
	036;exrsh
	'%; exmod
	'!; exnot
	'^; excmbin
	0;  0

excmbin:
	mov	r0,r3			/ give left flag of right
	br	eoprnd

exrsh:
	neg	r1
	beq	exlsh
	inc	r1
	clc
	ror	r2
exlsh:
	jsr	r5,combin; 0
	als	r1,r2
	br	eoprnd

exmod:
	jsr	r5,combin; 0
	mov	r1,-(sp)
	mov	r2,r1
	clr	r0
	dvd	(sp)+,r0
	mov	r1,r2
	br	eoprnd

exadd:
	jsr	r5,combin; 0
	add	r1,r2
	br	eoprnd

exsub:
	jsr	r5,combin; 1
	sub	r1,r2
	br	eoprnd

exand:
	jsr	r5,combin; 0
	com	r1
	bic	r1,r2
	br	eoprnd

exor:
	jsr	r5,combin; 0
	bis	r1,r2
	br	eoprnd

exmul:
	jsr	r5,combin; 0
	mpy	r2,r1
	mov	r1,r2
	br	eoprnd

exdiv:
	jsr	r5,combin; 0
	mov	r1,-(sp)
	mov	r2,r1
	clr	r0
	dvd	(sp)+,r0
	mov	r0,r2
	br	eoprnd

exnot:
	jsr	r5,combin; 0
	com	r1
	add	r1,r2
	br	eoprnd

eoprnd:
	mov	$'+,(sp)
	jmp	advanc

combin:
	mov	r0,-(sp)
	bis	r3,(sp)
	bic	$!40,(sp)
	bic	$!37,r0
	bic	$!37,r3
	cmp	r0,r3
	ble	1f
	mov	r0,-(sp)
	mov	r3,r0
	mov	(sp)+,r3
1:
	tst	r0
	beq	1f
	tst	(r5)+
	beq	2f
	cmp	r0,r3
	bne	2f
	mov	$1,r3
	br	2f
1:
	tst	(r5)+
	clr	r3
2:
	bis	(sp)+,r3
	rts	r5

/
/

/ a8 -- pdp-11 assembler pass 1

chartab:
	.byte -14,-14,-14,-14,-02,-14,-14,-14
	.byte -14,-22, -2,-14,-14,-22,-14,-14
	.byte -14,-14,-14,-14,-14,-14,-14,-14
	.byte -14,-14,-14,-14,-14,-14,-14,-14
	.byte -22,-20,-16,-14,-20,-20,-20,-12
	.byte -20,-20,-20,-20,-20,-20,056,-06
	.byte 060,061,062,063,064,065,066,067
	.byte 070,071,-20,-02,-00,-20,-14,-14
	.byte -14,101,102,103,104,105,106,107
	.byte 110,111,112,113,114,115,116,117
	.byte 120,121,122,123,124,125,126,127
	.byte 130,131,132,-20,-24,-20,-20,137
	.byte -14,141,142,143,144,145,146,147
	.byte 150,151,152,153,154,155,156,157
	.byte 160,161,162,163,164,165,166,167
	.byte 170,171,172,-14,-26,-14,176,-14

.data

namedone:.byte 0
a.tmp1:	</tmp/atm1a\0>
a.tmp2:	</tmp/atm2a\0>
a.tmp3:	</tmp/atm3a\0>
	.even
curfb:
	-1;-1;-1;-1;-1;-1;-1;-1;-1;-1
obufp:	outbuf
symend:	usymtab

.bss
curfbr:	.=.+10.
savdot:	.=.+6
bufcnt:	.=.+2
hshsiz = 1553.
hshtab:	.=2*hshsiz+.
pof:	.=.+1
wordf:	.=.+1
fin:	.=.+1
fbfil:	.=.+1
fileflg:.=.+1
errflg:	.=.+1
ch:	.=.+1
.even
symbol:	.=.+8.
obufc:	.=.+2
outbuf:	.=.+512.
line:	.=.+2
inbfcnt:.=.+2
ifflg:	.=.+2
inbfp:	.=.+2
nargs:	.=.+2
curarg:	.=.+2
opfound:.=.+2
savop:	.=.+2
numval:	.=.+2
nxtfb:	.=.+4
usymtab:.=.+36.
end:
.text
/
/

/ a9 -- pdp-11 assembler pass 1

eae = 0

/ key to types

/	0	undefined
/	1	absolute
/	2	text
/	3	data
/	4	bss
/	5	flop freg,dst (movfo, = stcfd)
/	6	branch
/	7	jsr
/	10	rts
/	11	sys
/	12	movf (=ldf,stf)
/	13	double operand (mov)
/	14	flop fsrc,freg (addf)
/	15	single operand (clr)
/	16	.byte
/	17	string (.ascii, "<")
/	20	.even
/	21	.if
/	22	.endif
/	23	.globl
/	24	register
/	25	.text
/	26	.data
/	27	.bss
/	30	mul,div, etc
/	31	sob
/	32	.comm
/	33	estimated text
/	34	estimated data
/	35	jbr
/	36	jeq, jne, etc

	.data
symtab:
/ special variables

<.\0\0\0\0\0\0\0>; dotrel:02; dot:000000
<..\0\0\0\0\0\0>;	01; dotdot:000000

/ register

<r0\0\0\0\0\0\0>;	24;000000
<r1\0\0\0\0\0\0>;	24;000001
<r2\0\0\0\0\0\0>;	24;000002
<r3\0\0\0\0\0\0>;	24;000003
<r4\0\0\0\0\0\0>;	24;000004
<r5\0\0\0\0\0\0>;	24;000005
<sp\0\0\0\0\0\0>;	24;000006
<pc\0\0\0\0\0\0>;	24;000007

.if eae

/eae & switches

<csw\0\0\0\0\0>;	01;177570
<div\0\0\0\0\0>;	01;177300
<ac\0\0\0\0\0\0>;	01;177302
<mq\0\0\0\0\0\0>;	01;177304
<mul\0\0\0\0\0>;	01;177306
<sc\0\0\0\0\0\0>;	01;177310
<sr\0\0\0\0\0\0>;	01;177311
<nor\0\0\0\0\0>;	01;177312
<lsh\0\0\0\0\0>;	01;177314
<ash\0\0\0\0\0>;	01;177316

.endif

/ system calls

<exit\0\0\0\0>;		01;0000001
<fork\0\0\0\0>;		01;0000002
<read\0\0\0\0>;		01;0000003
<write\0\0\0>;		01;0000004
<open\0\0\0\0>;		01;0000005
<close\0\0\0>;		01;0000006
<wait\0\0\0\0>;		01;0000007
<creat\0\0\0>;		01;0000010
<link\0\0\0\0>;		01;0000011
<unlink\0\0>;		01;0000012
<exec\0\0\0\0>;		01;0000013
<chdir\0\0\0>;		01;0000014
<time\0\0\0\0>;		01;0000015
<makdir\0\0>;		01;0000016
<chmod\0\0\0>;		01;0000017
<chown\0\0\0>;		01;0000020
<break\0\0\0>;		01;0000021
<stat\0\0\0\0>;		01;0000022
<seek\0\0\0\0>;		01;0000023
<tell\0\0\0\0>;		01;0000024
<mount\0\0\0>;		01;0000025
<umount\0\0>;		01;0000026
<setuid\0\0>;		01;0000027
<getuid\0\0>;		01;0000030
<stime\0\0\0>;		01;0000031
<fstat\0\0\0>;		01;0000034
<mdate\0\0\0>;		01;0000036
<stty\0\0\0\0>;		01;0000037
<gtty\0\0\0\0>;		01;0000040
<nice\0\0\0\0>;		01;0000042
<signal\0\0>;		01;0000060

/ double operand

<mov\0\0\0\0\0>;	13;0010000
<movb\0\0\0\0>;		13;0110000
<cmp\0\0\0\0\0>;	13;0020000
<cmpb\0\0\0\0>;		13;0120000
<bit\0\0\0\0\0>;	13;0030000
<bitb\0\0\0\0>;		13;0130000
<bic\0\0\0\0\0>;	13;0040000
<bicb\0\0\0\0>;		13;0140000
<bis\0\0\0\0\0>;	13;0050000
<bisb\0\0\0\0>;		13;0150000
<add\0\0\0\0\0>;	13;0060000
<sub\0\0\0\0\0>;	13;0160000

/ branch

<br\0\0\0\0\0\0>;	06;0000400
<bne\0\0\0\0\0>;	06;0001000
<beq\0\0\0\0\0>;	06;0001400
<bge\0\0\0\0\0>;	06;0002000
<blt\0\0\0\0\0>;	06;0002400
<bgt\0\0\0\0\0>;	06;0003000
<ble\0\0\0\0\0>;	06;0003400
<bpl\0\0\0\0\0>;	06;0100000
<bmi\0\0\0\0\0>;	06;0100400
<bhi\0\0\0\0\0>;	06;0101000
<blos\0\0\0\0>;		06;0101400
<bvc\0\0\0\0\0>;	06;0102000
<bvs\0\0\0\0\0>;	06;0102400
<bhis\0\0\0\0>;		06;0103000
<bec\0\0\0\0\0>;	06;0103000
<bcc\0\0\0\0\0>;	06;0103000
<blo\0\0\0\0\0>;	06;0103400
<bcs\0\0\0\0\0>;	06;0103400
<bes\0\0\0\0\0>;	06;0103400

/ jump/branch type

<jbr\0\0\0\0\0>;	35;0000400
<jne\0\0\0\0\0>;	36;0001000
<jeq\0\0\0\0\0>;	36;0001400
<jge\0\0\0\0\0>;	36;0002000
<jlt\0\0\0\0\0>;	36;0002400
<jgt\0\0\0\0\0>;	36;0003000
<jle\0\0\0\0\0>;	36;0003400
<jpl\0\0\0\0\0>;	36;0100000
<jmi\0\0\0\0\0>;	36;0100400
<jhi\0\0\0\0\0>;	36;0101000
<jlos\0\0\0\0>;		36;0101400
<jvc\0\0\0\0\0>;	36;0102000
<jvs\0\0\0\0\0>;	36;0102400
<jhis\0\0\0\0>;		36;0103000
<jec\0\0\0\0\0>;	36;0103000
<jcc\0\0\0\0\0>;	36;0103000
<jlo\0\0\0\0\0>;	36;0103400
<jcs\0\0\0\0\0>;	36;0103400
<jes\0\0\0\0\0>;	36;0103400

/ single operand

<clr\0\0\0\0\0>;	15;0005000
<clrb\0\0\0\0>;		15;0105000
<com\0\0\0\0\0>;	15;0005100
<comb\0\0\0\0>;		15;0105100
<inc\0\0\0\0\0>;	15;0005200
<incb\0\0\0\0>;		15;0105200
<dec\0\0\0\0\0>;	15;0005300
<decb\0\0\0\0>;		15;0105300
<neg\0\0\0\0\0>;	15;0005400
<negb\0\0\0\0>;		15;0105400
<adc\0\0\0\0\0>;	15;0005500
<adcb\0\0\0\0>;		15;0105500
<sbc\0\0\0\0\0>;	15;0005600
<sbcb\0\0\0\0>;		15;0105600
<tst\0\0\0\0\0>;	15;0005700
<tstb\0\0\0\0>;		15;0105700
<ror\0\0\0\0\0>;	15;0006000
<rorb\0\0\0\0>;		15;0106000
<rol\0\0\0\0\0>;	15;0006100
<rolb\0\0\0\0>;		15;0106100
<asr\0\0\0\0\0>;	15;0006200
<asrb\0\0\0\0>;		15;0106200
<asl\0\0\0\0\0>;	15;0006300
<aslb\0\0\0\0>;		15;0106300
<jmp\0\0\0\0\0>;	15;0000100
<swab\0\0\0\0>;		15;0000300

/ jsr

<jsr\0\0\0\0\0>;	07;0004000

/ rts

<rts\0\0\0\0\0>;	010;000200

/ simple operand

<sys\0\0\0\0\0>;	011;104400

/ flag-setting

<clc\0\0\0\0\0>;	01;0000241
<clv\0\0\0\0\0>;	01;0000242
<clz\0\0\0\0\0>;	01;0000244
<cln\0\0\0\0\0>;	01;0000250
<sec\0\0\0\0\0>;	01;0000261
<sev\0\0\0\0\0>;	01;0000262
<sez\0\0\0\0\0>;	01;0000264
<sen\0\0\0\0\0>;	01;0000270

/ floating point ops

<cfcc\0\0\0\0>;		01;170000
<setf\0\0\0\0>;		01;170001
<setd\0\0\0\0>;		01;170011
<seti\0\0\0\0>;		01;170002
<setl\0\0\0\0>;		01;170012
<clrf\0\0\0\0>;		15;170400
<negf\0\0\0\0>;		15;170700
<absf\0\0\0\0>;		15;170600
<tstf\0\0\0\0>;		15;170500
<movf\0\0\0\0>;		12;172400
<movif\0\0\0>;		14;177000
<movfi\0\0\0>;		05;175400
<movof\0\0\0>;		14;177400
<movfo\0\0\0>;		05;176000
<addf\0\0\0\0>;		14;172000
<subf\0\0\0\0>;		14;173000
<mulf\0\0\0\0>;		14;171000
<divf\0\0\0\0>;		14;174400
<cmpf\0\0\0\0>;		14;173400
<modf\0\0\0\0>;		14;171400
<movie\0\0\0>;		14;176400
<movei\0\0\0>;		05;175000
<ldfps\0\0\0>;		15;170100
<stfps\0\0\0>;		15;170200
<fr0\0\0\0\0\0>;	24;000000
<fr1\0\0\0\0\0>;	24;000001
<fr2\0\0\0\0\0>;	24;000002
<fr3\0\0\0\0\0>;	24;000003
<fr4\0\0\0\0\0>;	24;000004
<fr5\0\0\0\0\0>;	24;000005

/ 11/45 operations

<als\0\0\0\0\0>;	30;072000
<alsc\0\0\0\0>;		30;073000
<mpy\0\0\0\0\0>;	30;070000
.if eae-1
<mul\0\0\0\0\0>;	30;070000
<div\0\0\0\0\0>;	30;071000
<ash\0\0\0\0\0>;	30;072000
<ashc\0\0\0\0>;		30;073000
.endif
<dvd\0\0\0\0\0>;	30;071000
<xor\0\0\0\0\0>;	07;074000
<sxt\0\0\0\0\0>;	15;006700
<mark\0\0\0\0>;		11;006400
<sob\0\0\0\0\0>;	31;077000

/ specials

<.byte\0\0\0>;		16;000000
<.even\0\0\0>;		20;000000
<.if\0\0\0\0\0>;	21;000000
<.endif\0\0>;		22;000000
<.globl\0\0>;		23;000000
<.text\0\0\0>;		25;000000
<.data\0\0\0>;		26;000000
<.bss\0\0\0\0>;		27;000000
<.comm\0\0\0>;		32;000000

ebsymtab:
/ Below is following C-paradigm: if (signal(SIGINT, SIG_IGN) != SIG_IGN) signal(SIGINT, aexit)...
/ See page 126 in The UNIX programming environment, Kernighan/Pike on explanation
start:
	sys	signal; 2; 1      / Disable signal interrupt (2) by using odd (1) label
	ror	r0                / Old signal interrupt status is returned into r0, rotate right and place bit 0 into carry
	bcs	1f                / Branch to label 1 if carry is set and skip next 'sys signal' statement
	sys	signal; 2; aexit  / If we receive an interrupt signal during execution, jump to label aexit
1:
	mov	sp,r5             / stack pointer to r5
	mov	(r5)+,r0          / move pointed value in r5 (argc) to r0, increase r5 to point to next item on stack (as)
	cmpb	*2(r5),$'-    / *2(r5): r5+2 -> address to value. cmpb: (r5+2) - $'-, Z-bit set if diff is zero
	bne	1f                / branch to forward to label 1 if Z-bit is clear, ie (r5+2) not equal to $'-
	tst	(r5)+             / tst is equivalent of comparing the operand with zero: cmp (r5)+, $0
	dec	r0                / decrement r0 with 1 (argc -= 1)
	br	2f                / branch forward to label 2
1:
	clr	unglob            / clear memory for unglob (in as11.s) point at string "<-g/0>" through labels unglob and 3, argument '-' not used -> undefined symbols not global
2:
	movb	r0,nargs      / move byte r0 -> nargs (as18.s: nargs: .=.+2)
	mov	r5,curarg         / move r5 (sp) -> curarg (as18.s: curarg:	.=.+2)
	jsr	r5,fcreat; a.tmp1 / jump to fcreat (as11.s) to create file a.tmp1. r5 holds a pointer to next statement
	movb	r0,pof        / move r0 -> pof (as18.s: pof: .=.+1), return value from fcreat in r0 (file descriptor)
	jsr	r5,fcreat; a.tmp2 / jump to fcreat (as11.s) to create file a.tmp2
	movb	r0,fbfil      / move byte r0 -> fbfil (as18.s: fbfil: .=.+1)
	jsr	pc,setup          / jump subroutine setup: push pc to stack and move sp to point there, pc set to pc + 2
	jmp	go                / jump to go (as11.s)

setup:
	mov	$symtab,r1        / move location of symtab -> r1
1:
	clr	r3                / clear r3
	mov	$8,r2             / move 8 -> r2 (strings in symtab are 8 char long)
	mov	r1,-(sp)          / push r1 to stack: move location of symtab to stack
2:
	movb	(r1)+,r4      / move (byte) value pointed to by r1 (symtab) -> r4 (<.\0\0\0\0\0\0\0>), increment r1 (next char), z-bit set if (r1) is zero
	beq	2f                / branch forward to label 2 if z-bit is 1
	add	r4,r3             / r3 = r4 + r3 (ord(.) + 0)
	swab	r3            / swap high/low bytes in r3 (. in high byte)
	sob	r2,2b             / subtract 1 from r2, branch backwards to label 2: if r2 is not zero
2:
	clr	r2                / clear r2
	div	$hshsiz,r2        / divide r2 / $hshsiz (1553), store quotient in r2 and reminder in r3
	ashc	$1,r2         / arithmetic shift combined, shift left 1 r3 (low word) and r2 (high word)
	add	$hshtab,r3        / r3 = $hshtab + r3
4:
	sub	r2,r3
	cmp	r3,$hshtab
	bhi	3f
	add	$2*hshsiz,r3
3:
	tst	-(r3)
	bne	4b
	mov	(sp)+,r1
	mov	r1,(r3)
	add	$12.,r1
	cmp	r1,$ebsymtab
	blo	1b
	rts	pc

/overlay buffer
inbuf	= setup
.	=inbuf+512.

