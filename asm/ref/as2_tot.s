/
/

/ a21 -- pdp-11 assembler pass 2 

indir	= 0

main:
	sys	signal; 2; 1
	ror	r0
	bcs	1f
	sys	signal; 2; aexit
1:
	jmp	start

/ set up sizes and origins

go:

/ read in symbol table

	mov	$usymtab,r1
1:
	jsr	pc,getw
	bvs	1f
	add	$14,symsiz		/ count symbols
	jsr	pc,getw
	jsr	pc,getw
	jsr	pc,getw
	jsr	pc,getw
	mov	r4,r0
	bic	$!37,r0
	cmp	r0,$2			/text
	blo	2f
	cmp	r0,$3			/data
	bhi	2f
	add	$31,r4			/mark "estimated"
	mov	r4,(r1)+
	jsr	pc,getw
	mov	r4,(r1)+
	br	3f
2:
	clr	(r1)+
	clr	(r1)+
	jsr	pc,getw
3:
	jsr	pc,setbrk
	br	1b
1:

/ read in f-b definitions

	mov	r1,fbbufp
	movb	fbfil,fin
	clr	ibufc
1:
	jsr	pc,getw
	bvs	1f
	add	$31,r4			/ "estimated"
	mov	r4,(r1)+
	jsr	pc,getw
	mov	r4,(r1)+
	jsr	pc,setbrk
	br	1b
1:
	mov	r1,endtable
	mov	$100000,(r1)+

/ set up input text file; initialize f-b table

	jsr	pc,setup
/ do pass 1

	jsr	pc,assem

/ prepare for pass 2
	cmp	outmod,$777
	beq	1f
	jmp	aexit
1:
	clr	dot
	mov	$2,dotrel
	mov	$..,dotdot
	clr	brtabp
	movb	fin,r0
	sys	close
	jsr	r5,ofile; a.tmp1
	movb	r0,fin
	clr	ibufc
	jsr	pc,setup
	inc	passno
	inc	bsssiz
	bic	$1,bsssiz
	mov	txtsiz,r1
	inc	r1
	bic	$1,r1
	mov	r1,txtsiz
	mov	datsiz,r2
	inc	r2
	bic	$1,r2
	mov	r2,datsiz
	mov	r1,r3
	mov	r3,datbase	/ txtsiz
	mov	r3,savdot+2
	add	r2,r3
	mov	r3,bssbase	/ txtsiz+datsiz
	mov	r3,savdot+4
	asl	r3
	add	$20,r3
	mov	r3,symseek	/ 2*txtsiz+2*datsiz+20
	sub	r2,r3
	mov	r3,drelseek	/ 2*txtsiz+datsiz
	sub	r1,r3
	mov	r3,trelseek	/ txtsiz+datsiz+20
	sub	r2,r3
	mov	r3,datseek	/ txtsiz+20
	mov	$usymtab,r1
1:
	jsr	pc,doreloc
	add	$4,r1
	cmp	r1,endtable
	blo	1b
	clr	r0
	jsr	r5,oset; txtp
	mov	trelseek,r0
	jsr	r5,oset; relp
	mov	$8.,r2
	mov	$txtmagic,r1
1:
	mov	(r1)+,r0
	jsr	r5,putw; txtp
	dec	r2
	bne	1b
	jsr	pc,assem

/polish off text and relocation

	jsr	r5,flush; txtp
	jsr	r5,flush; relp

/ append full symbol table

	mov	symf,r0
	mov	r0,fin
	sys	seek; 0; 0;
	clr	ibufc
	mov	symseek,r0
	jsr	r5,oset; txtp
	mov	$usymtab,r1
1:
	jsr	pc,getw
	bvs	1f
	mov	r4,r0
	jsr	r5,putw; txtp
	jsr	pc,getw
	mov	r4,r0
	jsr	r5,putw; txtp
	jsr	pc,getw
	mov	r4,r0
	jsr	r5,putw; txtp
	jsr	pc,getw
	mov	r4,r0
	jsr	r5,putw; txtp
	mov	(r1)+,r0
	jsr	r5,putw; txtp
	mov	(r1)+,r0
	jsr	r5,putw; txtp
	jsr	pc,getw
	jsr	pc,getw
	br	1b
1:
	jsr	r5,flush; txtp
	jmp	aexit

	.data
aexit:
	mov	a.tmp1,0f
	sys	unlink; 0:..
	mov	a.tmp2,0f
	sys	unlink; 0:..
	mov	a.tmp3,0f
	sys	unlink; 0:..
	sys	chmod; a.out; outmod: 777
	sys	exit
	.text

filerr:
	mov	*(r5),r5
1:
	movb	(r5)+,ch
	beq	1f
	mov	$1,r0
	sys	write; ch; 1
	br	1b
1:
	mov	$1,r0
	sys	write; qnl; 2
	jmp	aexit

doreloc:
	movb	(r1),r0
	bne	1f
	bisb	defund,(r1)
1:
	bic	$!37,r0
	cmp	r0,$5
	bhis	1f
	cmp	r0,$3
	blo	1f
	beq	2f
	add	bssbase,2(r1)
	rts	pc
2:
	add	datbase,2(r1)
1:
	rts	pc

setbrk:
	mov	r1,-(sp)
	add	$20,r1
	cmp	r1,0f
	blo	1f
	add	$512.,0f
	sys	indir; 9f
	.data
9:	sys	break; 0: end
	.text
1:
	mov	(sp)+,r1
	rts	pc

setup:
	mov	$curfb,r4
1:
	clr	(r4)+
	cmp	r4,$curfb+40.
	blo	1b
	mov	txtfil,fin
	clr	ibufc
	clr	r4
1:
	jsr	pc,fbadv
	tstb	(r4)+
	cmp	r4,$10.
	blt	1b
	rts	pc

ofile:
	mov	*(r5),0f
	sys	indir; 9f
	.data
9:	sys	open; 0:..; 0
	.text
	bes	1f
	tst	(r5)+
	rts	r5
1:
	jmp	filerr
/
/

/ a2 -- pdp-11 assembler pass 2

outw:
	cmp	dot-2,$4
	beq	9f
	bit	$1,dot
	bne	1f
	add	$2,dot
	tstb	passno
	beq	8f
	clr	-(sp)
	rol	r3
	adc	(sp)
	asr	r3		/ get relative pc bit
	cmp	r3,$40
	bne	2f
/ external references
	mov	$666,outmod		/ make nonexecutable
	mov	xsymbol,r3
	sub	$usymtab,r3
	asl	r3
	bis	$4,r3		/ external relocation
	br	3f
2:
	bic	$40,r3		/ clear any ext bits
	cmp	r3,$5
	blo	4f
	cmp	r3,$33		/ est. text, data
	beq	6f
	cmp	r3,$34
	bne	7f
6:
	jsr	r5,error; 'r
7:
	mov	$1,r3		/ make absolute
4:
	cmp	r3,$2
	blo	5f
	cmp	r3,$4
	bhi	5f
	tst	(sp)
	bne	4f
	add	dotdot,r2
	br	4f
5:
	tst	(sp)
	beq	4f
	sub	dotdot,r2
4:
	dec	r3
	bpl	3f
	clr	r3
3:
	asl	r3
	bis	(sp)+,r3
	mov	r2,r0
	jsr	r5,putw; txtp
	add	$2,*tseekp
	mov	r3,r0
	jsr	r5,putw; relp
	add	$2,*rseekp
8:
	rts	pc
1:
	jsr	r5,error; 'o
	clr	r3
	jsr	pc,outb
	rts	pc

9:
	jsr	r5,error; 'x
	rts	pc

outb:
	cmp	dot-2,$4		/ test bss mode
	beq	9b
	cmp	r3,$1
	blos	1f
	jsr	r5,error; 'r
1:
	tstb	passno
	beq	2f
	mov	r2,r0
	bit	$1,dot
	bne	1f
	jsr	r5,putw; txtp
	clr	r0
	jsr	r5,putw; relp
	add	$2,*rseekp
	add	$2,*tseekp
	br	2f
1:
	mov	txtp,r0
	movb	r2,-1(r0)
2:
	inc	dot
	rts	pc

error:
	mov	$666,outmod		/ make nonexecutable
	mov	r3,-(sp)
	mov	r2,-(sp)
	mov	r1,-(sp)
	mov	r0,-(sp)
	mov	$argb,r1
1:
	movb	(r1),ch
	beq	1f
	clrb	(r1)+
	mov	$1,r0
	sys	write; ch; 1
	br	1b
1:
	mov	(r5)+,r0
	movb	r0,0f
	mov	line,r3
	mov	$0f+6,r0
	mov	$4,r1
2:
	clr	r2
	dvd	$10.,r2
	add	$'0,r3
	movb	r3,-(r0)
	mov	r2,r3
	sob	r1,2b
	mov	$1,r0
	sys	write; 0f; 7
	mov	(sp)+,r0
	mov	(sp)+,r1
	mov	(sp)+,r2
	mov	(sp)+,r3
	rts	r5

	.data
0:	<f xxxx\n>
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

/
/

/ a3 -- pdp-11 assembler pass 2

assem:
	jsr	pc,readop
	cmp	r4,$5
	beq	2f
	cmp	r4,$'<
	beq	2f
	jsr	pc,checkeos
		br eal1
	mov	r4,-(sp)
	cmp	(sp),$1
	bne	1f
	mov	$2,(sp)
	jsr	pc,getw
	mov	r4,numval
1:
	jsr	pc,readop
	cmp	r4,$'=
	beq	4f
	cmp	r4,$':
	beq	1f
	mov	r4,savop
	mov	(sp)+,r4
2:
	jsr	pc,opline
dotmax:
	tstb	passno
	bne	eal1
	movb	dotrel,r0
	asl	r0
	cmp	dot,txtsiz-4(r0)
	blos	ealoop
	mov	dot,txtsiz-4(r0)
eal1:
	jmp	ealoop
1:
	mov	(sp)+,r4
	cmp	r4,$200
	bhis	1f
	cmp	r4,$2
	beq	3f
	jsr	r5,error; 'x
	br	assem
1:
	tstb	passno
	bne	2f
	movb	(r4),r0
	bic	$!37,r0
	beq	5f
	cmp	r0,$33
	blt	6f
	cmp	r0,$34
	ble	5f
6:
	jsr	r5,error; 'm
5:
	bic	$37,(r4)
	bis	dotrel,(r4)
	mov	2(r4),brdelt
	sub	dot,brdelt
	mov	dot,2(r4)
	br	assem
2:
	cmp	dot,2(r4)
	beq	assem
	jsr	r5,error; 'p
	br	assem
3:
	mov	numval,r4
	jsr	pc,fbadv
	asl	r4
	mov	curfb(r4),r0
	movb	dotrel,(r0)
	mov	2(r0),brdelt
	sub	dot,brdelt
	mov	dot,2(r0)
	br	assem
4:
	jsr	pc,readop
	jsr	pc,expres
	mov	(sp)+,r1
	cmp	r1,$symtab	/test for dot
	bne	1f
	bic	$40,r3
	cmp	r3,dotrel	/ can't change relocation
	bne	2f
	cmp	r3,$4		/ bss
	bne	3f
	mov	r2,dot
	br	dotmax
3:
	sub	dot,r2
	bmi	2f
	mov	r2,-(sp)
3:
	dec	(sp)
	bmi	3f
	clr	r2
	mov	$1,r3
	jsr	pc,outb
	br	3b
3:
	tst	(sp)+
	br	dotmax
2:
	jsr	r5,error; '.
	br	ealoop
1:
	cmp	r3,$40
	bne	1f
	jsr	r5,error; 'r
1:
	bic	$37,(r1)
	bic	$!37,r3
	bne	1f
	clr	r2
1:
	bisb	r3,(r1)
	mov	r2,2(r1)

ealoop:
	cmp	r4,$'\n
	beq	1f
	cmp	r4,$'\e
	bne	9f
	rts	pc
1:
	inc	line
9:
	jmp	assem

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

fbadv:
	asl	r4
	mov	nxtfb(r4),r1
	mov	r1,curfb(r4)
	bne	1f
	mov	fbbufp,r1
	br	2f
1:
	add	$4,r1
2:
	cmpb	1(r1),r4
	beq	1f
	tst	(r1)
	bpl	1b
1:
	mov	r1,nxtfb(r4)
	asr	r4
	rts	pc

/
/

/ a4 -- pdp-11 assembler pass 2

oset:
	mov	r2,-(sp)
	mov	(r5)+,r1
	mov	r0,r2
	bic	$!777,r0
	add	r1,r0
	add	$6,r0
	mov	r0,(r1)+	/ next slot
	mov	r1,r0
	add	$1004,r0
	mov	r0,(r1)+	/ buf max
	mov	r2,(r1)+	/ seek addr
	mov	(sp)+,r2
	rts	r5

putw:
	mov	r1,-(sp)
	mov	r2,-(sp)
	mov	(r5)+,r2
	mov	(r2)+,r1	/ slot
	cmp	r1,(r2)		/ buf max
	bhis	1f
	mov	r0,(r1)+
	mov	r1,-(r2)
	br	2f
1:
	tst	(r2)+
	mov	r0,-(sp)
	jsr	r5,flush1
	mov	(sp)+,r0
	mov	r0,*(r2)+
	add	$2,-(r2)
2:
	mov	(sp)+,r2
	mov	(sp)+,r1
	rts	r5

flush:
	mov	(r5)+,r2
	cmp	(r2)+,(r2)+
flush1:
	mov	(r2)+,r1
	mov	r1,0f		/ seek address
	mov	fout,r0
	sys	indir; 9f
	.data
9:	sys	seek; 0:..; 0
	.text
	bic	$!777,r1
	add	r2,r1		/ write address
	mov	r1,0f
	mov	r2,r0
	bis	$777,-(r2)
	inc	(r2)		/ new seek addr
	cmp	-(r2),-(r2)
	sub	(r2),r1
	neg	r1
	mov	r1,0f+2		/ count
	mov	r0,(r2)		/ new next slot
	mov	fout,r0
	sys	indir; 9f
	.data
9:	sys	write; 0:..; ..
	.text
	rts	r5

readop:
	mov	savop,r4
	beq	1f
	clr	savop
	rts	pc
1:
	jsr	pc,getw1
	cmp	r4,$200
	blo	1f
	cmp	r4,$4000
	blo	2f
	add	$usymtab-4000,r4
	rts	pc
2:
	add	$symtab-1000,r4
1:
	rts	pc

getw:
	mov	savop,r4
	beq	getw1
	clr	savop
	rts	pc
getw1:
	dec	ibufc
	bgt	1f
	movb	fin,r0
	sys	read; inbuf; 512.
	bes	3f
	asr	r0
	mov	r0,ibufc
	bne	2f
3:
	mov	$4,r4
	sev
	rts	pc
2:
	mov	$inbuf,ibufp
1:
	mov	*ibufp,r4
	add	$2,ibufp
	rts	pc
/
/

/ as25 is empty
/
/

/ a6 -- pdp-11 assembler pass 2

opline:
	mov	r4,r0
	jsr	r5,betwen; 0; 177
		br 2f
	cmp	r4,$5
	beq	opeof
	cmp	r4,$'<
	bne	xpr
	jmp	opl17
xxpr:
	tst	(sp)+
xpr:
	jsr	pc,expres
	jsr	pc,outw
	rts	pc
2:
	movb	(r4),r0
	cmp	r0,$24		/reg
	beq	xpr
	cmp	r0,$33		/est text
	beq	xpr
	cmp	r0,$34		/ est data
	beq	xpr
	jsr	r5,betwen; 5; 36
		br xpr
	mov	2(r4),-(sp)
	mov	r0,-(sp)
	jsr	pc,readop
	mov	(sp)+,r0
	asl	r0
	mov	$adrbuf,r5
	clr	swapf
	mov	$-1,rlimit
	jmp	*1f-10.(r0)

1:
	opl5
	opl6
	opl7
	opl10
	opl11
	opl12
	opl13
	opl14
	opl15
	opl16
	opl17
	opl20
	opl21
	opl22
	opl23
	xxpr
	opl25
	opl26
	opl27
	opl30
	opl31
	opl32
	xxpr
	xxpr
	opl35
	opl36

opeof:
	mov	$1,line
	mov	$20,-(sp)
	mov	$argb,r1
1:
	jsr	pc,getw
	tst	r4
	bmi	1f
	movb	r4,(r1)+
	dec	(sp)
	bgt	1b
	tstb	-(r1)
	br	1b
1:
	movb	$'\n,(r1)+
	clrb	(r1)+
	tst	(sp)+
	rts	pc

opl30:	/ mpy, dvd etc
	inc	swapf
	mov	$1000,rlimit
	br	opl13

opl14:		/ flop freg,fsrc
	inc	swapf

opl5:		/ flop src,freg
	mov	$400,rlimit

/double
opl13:
	jsr	pc,addres
op2a:
	mov	r2,-(sp)
	jsr	pc,readop
op2b:
	jsr	pc,addres
	tst	swapf
	beq	1f
	mov	(sp),r0
	mov	r2,(sp)
	mov	r0,r2
1:
	swab	(sp)
	asr	(sp)
	asr	(sp)
	cmp	(sp),rlimit
	blo	1f
	jsr	r5,error; 'x
1:
	bis	(sp)+,r2
	bis	(sp)+,r2
	clr	r3
	jsr	pc,outw
	mov	$adrbuf,r1
1:
	cmp	r1,r5
	bhis	1f
	mov	(r1)+,r2
	mov	(r1)+,r3
	mov	(r1)+,xsymbol
	jsr	pc,outw
	br	1b
1:
	rts	pc

opl15:		/ single operand
	clr	-(sp)
	br	op2b

opl12:		/ movf
	mov	$400,rlimit
	jsr	pc,addres
	cmp	r2,$4		/ see if source is fregister
	blo	1f
	inc	swapf
	br	op2a
1:
	mov	$174000,(sp)
	br	op2a

/ jbr
opl35:
/ jeq, jne, etc
opl36:
	jsr	pc,expres
	tstb	passno
	bne	1f
	mov	r2,r0
	jsr	pc,setbr
	tst	r2
	beq	2f
	cmp	(sp),$br
	beq	2f
	add	$2,r2
2:
	add	r2,dot		/ if doesn't fit
	add	$2,dot
	tst	(sp)+
	rts	pc
1:
	jsr	pc,getbr
	bcc	dobranch
	mov	(sp)+,r0
	mov	r2,-(sp)
	mov	r3,-(sp)
	cmp	r0,$br
	beq	2f
	mov	$402,r2
	xor	r0,r2		/ flip cond, add ".+6"
	mov	$1,r3
	jsr	pc,outw
2:
	mov	$1,r3
	mov	$jmp+37,r2
	jsr	pc,outw
	mov	(sp)+,r3
	mov	(sp)+,r2
	jsr	pc,outw
	rts	pc

/sob
opl31:	/ sob
	jsr	pc,expres
	jsr	pc,checkreg
	swab	r2
	asr	r2
	asr	r2
	bis	r2,(sp)
	jsr	pc,readop
	jsr	pc,expres
	tstb	passno
	beq	3f
	sub	dot,r2
	neg	r2
	mov	r2,r0
	jsr	r5,betwen; -2; 175
		br 2f
	add	$4,r2
	br	1f

/branch
opl6:
	jsr	pc,expres
	tstb	passno
	beq	3f
dobranch:
	sub	dot,r2
	mov	r2,r0
	jsr	r5,betwen; -254.; 256.
		br 2f
1:
	bit	$1,r2
	bne	2f
	cmp	r3,dot-2	/ same relocation as .
	bne	2f
	asr	r2
	dec	r2
	bic	$177400,r2
3:
	bis	(sp)+,r2
	clr	r3
	jsr	pc,outw
	rts	pc
2:
	jsr	r5,error; 'b
	clr	r2
	br	3b

/jsr
opl7:
	jsr	pc,expres
	jsr	pc,checkreg
	jmp	op2a

/ rts
opl10:
	jsr	pc,expres
	jsr	pc,checkreg
	br	1f

/ sys, emt etc
opl11:
	jsr	pc,expres
	cmp	r2,$64.
	bhis	0f
	cmp	r3,$1
	ble	1f
0:
	jsr	pc,errora
1:
	bis	(sp)+,r2
	jsr	pc,outw
	rts	pc

/ .byte
opl16:
	jsr	pc,expres
	jsr	pc,outb
	cmp	r4,$',
	bne	1f
	jsr	pc,readop
	br	opl16
1:
	tst	(sp)+
	rts	pc

/ < (.ascii)
opl17:
	jsr	pc,getw
	mov	$1,r3
	mov	r4,r2
	bmi	2f
	bic	$!377,r2
	jsr	pc,outb
	br	opl17
2:
	jsr	pc,getw
	rts	pc

/.even
opl20:
	bit	$1,dot
	beq	1f
	cmp	dot-2,$4
	beq	2f		/ bss mode
	clr	r2
	clr	r3
	jsr	pc,outb
	br	1f
2:
	inc	dot
1:
	tst	(sp)+
	rts	pc
opl21:	/if
	jsr	pc,expres
opl22:
oplret:
	tst	(sp)+
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
	tst	(sp)+
	rts	pc

/ .text, .data, .bss
opl25:
opl26:
opl27:
	inc	dot
	bic	$1,dot
	mov	r0,-(sp)
	mov	dot-2,r1
	asl	r1
	mov	dot,savdot-4(r1)
	tstb	passno
	beq	1f
	jsr	r5,flush; txtp
	jsr	r5,flush; relp
	mov	(sp),r2
	add	$txtseek-[2*25],r2
	mov	r2,tseekp
	mov	(r2),r0
	jsr	r5,oset; txtp
	add	$trelseek-txtseek,r2
	mov	(r2),r0
	mov	r2,rseekp
	jsr	r5,oset; relp
1:
	mov	(sp)+,r0
	mov	savdot-[2*25](r0),dot
	asr	r0
	sub	$25-2,r0
	mov	r0,dot-2	/ new . relocation
	tst	(sp)+
	rts	pc

opl32:
	cmp	r4,$200
	blo	1f
	mov	r4,-(sp)
	jsr	pc,readop
	jsr	pc,readop
	jsr	pc,expres
	mov	(sp)+,r0
	bit	$37,(r0)
	bne	1f
	bis	$40,(r0)
	mov	r2,2(r0)
1:
	tst	(sp)+
	rts	pc

addres:
	clr	-(sp)
4:
	cmp	r4,$'(
	beq	alp
	cmp	r4,$'-
	beq	amin
	cmp	r4,$'$
	beq	adoll
	cmp	r4,$'*
	bne	getx
	jmp	astar
getx:
	jsr	pc,expres
	cmp	r4,$'(
	bne	2f
	jsr	pc,readop
	mov	r2,(r5)+
	mov	r3,(r5)+
	mov	xsymbol,(r5)+
	jsr	pc,expres
	jsr	pc,checkreg
	jsr	pc,checkrp
	bis	$60,r2
	bis	(sp)+,r2
	rts	pc

2:
	cmp	r3,$24
	bne	1f
	jsr	pc,checkreg
	bis	(sp)+,r2
	rts	pc
1:
	mov	r3,-(sp)
	bic	$40,r3
	mov	(sp)+,r3
	bis	$100000,r3
	sub	dot,r2
	sub	$4,r2
	cmp	r5,$adrbuf
	beq	1f
	sub	$2,r2
1:
	mov	r2,(r5)+		/ index
	mov	r3,(r5)+		/ index reloc.
	mov	xsymbol,(r5)+		/ index global
	mov	$67,r2			/ address mode
	bis	(sp)+,r2
	rts	pc

alp:
	jsr	pc,readop
	jsr	pc,expres
	jsr	pc,checkrp
	jsr	pc,checkreg
	cmp	r4,$'+
	beq	1f
	tst	(sp)+
	beq	2f
	bis	$70,r2
	clr	(r5)+
	clr	(r5)+
	mov	xsymbol,(r5)+
	rts	pc
2:
	bis	$10,r2
	rts	pc
1:
	jsr	pc,readop
	bis	$20,r2
	bis	(sp)+,r2
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
	bis	(sp)+,r2
	bis	$40,r2
	rts	pc

adoll:
	jsr	pc,readop
	jsr	pc,expres
	mov	r2,(r5)+
	mov	r3,(r5)+
	mov	xsymbol,(r5)+
	mov	(sp)+,r2
	bis	$27,r2
	rts	pc

astar:
	tst	(sp)
	beq	1f
	jsr	r5,error; '*
1:
	mov	$10,(sp)
	jsr	pc,readop
	jmp	4b

errora:
	jsr	r5,error; 'a
	rts	pc

checkreg:
	cmp	r2,$7
	bhi	1f
	cmp	r1,$1
	blos	2f
	cmp	r3,$5
	blo	1f
2:
	rts	pc
1:
	jsr	pc,errora
	clr	r2
	clr	r3
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

setbr:
	mov	brtabp,r1
	cmp	r1,$brlen
	blt	1f
	mov	$2,r2
	rts	pc
1:
	inc	brtabp
	clr	-(sp)
	sub	dot,r0
	ble	1f
	sub	brdelt,r0
1:
	jsr	r5,betwen; -254.; 256.
		br 1f
	br	2f
1:
	mov	r1,-(sp)
	bic	$!7,(sp)
	mov	$1,r0
	ash	(sp)+,r0
	ash	$-3,r1
	bisb	r0,brtab(r1)
	mov	$2,(sp)
2:
	mov	(sp)+,r2
	rts	pc

getbr:
	mov	brtabp,r1
	cmp	r1,$brlen
	blt	1f
	sec
	rts	pc
1:
	mov	r1,-(sp)
	bic	$!7,(sp)
	neg	(sp)
	inc	brtabp
	ash	$-3,r1
	movb	brtab(r1),r1
	ash	(sp)+,r1
	ror	r1		/ 0-bit into c-bit
	rts	pc
/
/

/  a7 -- pdp-11 assembler

expres:
	clr	xsymbol
expres1:
	mov	r5,-(sp)
	mov	$'+,-(sp)
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
	tst	r0
	bne	1f
	tstb	passno
	beq	1f
	jsr	r5,error; 'u
1:
	cmp	r0,$40
	bne	1f
	mov	r4,xsymbol
	clr	r1
	br	oprand
1:
	mov	2(r4),r1
	br	oprand
7:
	cmp	r4,$141
	blo	1f
	asl	r4
	mov	curfb-[2*141](r4),r0
	mov	2(r0),r1
	movb	(r0),r0
	br	oprand
1:
	mov	$esw1,r1
1:
	cmp	(r1)+,r4
	beq	1f
	tst	(r1)+
	bne	1b
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
	2;	exnum1
	'!;	binop
	200;	0

binop:
	cmpb	(sp),$'+
	beq	1f
	jsr	pc,errore
1:
	movb	r4,(sp)
	br	advanc

exnum1:
	mov	numval,r1
	br	1f

exnum:
	jsr	pc,getw
	mov	r4,r1
1:
	mov	$1,r0
	br	oprand

brack:
	mov	r2,-(sp)
	mov	r3,-(sp)
	jsr	pc,readop
	jsr	pc,expres1
	cmp	r4,$']
	beq	1f
	jsr	r5,error; ']
1:
	mov	r3,r0
	mov	r2,r1
	mov	(sp)+,r3
	mov	(sp)+,r2

oprand:
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
	'^; excmbin
	'!; exnot
	200;  0

excmbin:
	mov	r0,r3
	br	eoprnd

exrsh:
	neg	r1
	beq	exlsh
	inc	r1
	clc
	ror	r2
exlsh:
	jsr	r5,combin; relte2
	als	r1,r2
	br	eoprnd

exmod:
	jsr	r5,combin; relte2
	mov	r3,r0
	mov	r2,r3
	clr	r2
	dvd	r1,r2
	mov	r3,r2
	mov	r0,r3
	br	eoprnd

exadd:
	jsr	r5,combin; reltp2
	add	r1,r2
	br	eoprnd

exsub:
	jsr	r5,combin; reltm2
	sub	r1,r2
	br	eoprnd

exand:
	jsr	r5,combin; relte2
	com	r1
	bic	r1,r2
	br	eoprnd

exor:
	jsr	r5,combin; relte2
	bis	r1,r2
	br	eoprnd

exmul:
	jsr	r5,combin; relte2
	mpy	r2,r1
	mov	r1,r2
	br	eoprnd

exdiv:
	jsr	r5,combin; relte2
	mov	r3,r0
	mov	r2,r3
	clr	r2
	dvd	r1,r2
	mov	r0,r3
	br	eoprnd

exnot:
	jsr	r5,combin; relte2
	com	r1
	add	r1,r2
	br	eoprnd

eoprnd:
	mov	$'+,(sp)
	jmp	advanc

combin:
	tstb	passno
	bne	combin1
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
	cmp	(r5)+,$reltm2
	bne	2f
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
combin1:
	mov	r1,-(sp)
	clr	maxtyp
	jsr	pc,maprel
	mov	r0,r1
	mpy	$6,r1
	mov	r3,r0
	jsr	pc,maprel
	add	(r5)+,r0
	add	r1,r0
	movb	(r0),r3
	bpl	1f
	cmp	r3,$-1
	beq	2f
	jsr	r5,error; 'r
2:
	mov	maxtyp,r3
1:
	mov	(sp)+,r1
	rts	r5

maprel:
	cmp	r0,$40
	bne	1f
	mov	$5,r0
	rts	pc
1:
	bic	$!37,r0
	cmp	r0,maxtyp
	blos	1f
	mov	r0,maxtyp
1:
	cmp	r0,$5
	blos	1f
	mov	$1,r0
1:
	rts	pc

X = -2
M = -1
reltp2:
	.byte 0, 0, 0, 0, 0, 0
	.byte 0, M, 2, 3, 4,40
	.byte 0, 2, X, X, X, X
	.byte 0, 3, X, X, X, X
	.byte 0, 4, X, X, X, X
	.byte 0,40, X, X, X, X

reltm2:
	.byte 0, 0, 0, 0, 0, 0
	.byte 0, M, 2, 3, 4,40
	.byte 0, X, 1, X, X, X
	.byte 0, X, X, 1, X, X
	.byte 0, X, X, X, 1, X
	.byte 0, X, X, X, X, X

relte2:
	.byte 0, 0, 0, 0, 0, 0
	.byte 0, M, X, X, X, X
	.byte 0, X, X, X, X, X
	.byte 0, X, X, X, X, X
	.byte 0, X, X, X, X, X
	.byte 0, X, X, X, X, X

/
/

/ as8 -- PDP-11 assembler pass 2

qnl:	<?\n>
a.out:	<a.out\0>

.even
a.outp:	a.out

	.data
a.tmp1:	0
a.tmp2:	0
a.tmp3:	0

tseekp:	txtseek
rseekp:	trelseek

txtmagic:
	br	.+20
txtsiz:	.=.+2
datsiz:	.=.+2
bsssiz:	.=.+2
symsiz:	.=.+2
stksiz:	.=.+2
exorig:	.=.+2
	.=.+2

txtseek: 20
datseek:.=.+2
	.=.+2
trelseek:.=.+2
drelseek:.=.+2
	.=.+2
symseek:.=.+2

.bss

brlen	= 1024.
brtab:	.=.+[brlen\/8.]
brtabp:	.=.+2
brdelt:	.=.+2
fbbufp:	.=.+2
defund:	.=.+2
savdot:	.=.+6
datbase:.=.+2
bssbase:.=.+2
fbfil:	.=.+2
fin:	.=.+2
ibufc:	.=.+2
txtfil:	.=.+2
symf:	.=.+2
adrbuf:	.=.+12.
xsymbol:.=.+2
fout:	.=.+2
ch:	.=.+2
wordf:	.=.+2
argb:	.=.+22.
line:	.=.+2
savop:	.=.+2
curfb:	.=.+20.
nxtfb:	.=.+20.
numval:	.=.+2
maxtyp:	.=.+2
relfil:	.=.+2
ibufp:	.=.+2
txtp:	.=.+6+512.
relp:	.=.+6+512.
swapf:	.=.+2
rlimit:	.=.+2
passno:	.=.+2
endtable:.=.+2
usymtab:.=.+20.
end:

.text
/
/

/ as9 -- PDP-11 assembler pass 2

eae = 0

	.data
symtab:

/ special variables

dotrel: 02; dot:000000 /.
 01; dotdot:000000 /..

/ register

24;000000 /r0
24;000001 /r1
24;000002 /r2
24;000003 /r3
24;000004 /r4
24;000005 /r5
24;000006 /sp
24;000007 /pc


.if eae
/eae & switches

01;177570 /csw
01;177300 /div
01;177302 /ac
01;177304 /mq
01;177306 /mul
01;177310 /sc
01;177311 /sr
01;177312 /nor
01;177314 /lsh
01;177316 /ash

.endif

/ system calls

01;0000001 /exit
01;0000002 /fork
01;0000003 /read
01;0000004 /write
01;0000005 /open
01;0000006 /close
01;0000007 /wait
01;0000010 /creat
01;0000011 /link
01;0000012 /unlink
01;0000013 /exec
01;0000014 /chdir
01;0000015 /time
01;0000016 /makdir
01;0000017 /chmod
01;0000020 /chown
01;0000021 /break
01;0000022 /stat
01;0000023 /seek
01;0000024 /tell
01;0000025 /mount
01;0000026 /umount
01;0000027 /setuid
01;0000030 /getuid
01;0000031 /stime
01;0000034 /fstat
01;0000036 /mdate
01;0000037 /stty
01;0000040 /gtty
01;0000042 /nice
01;0000060 /signal

/ double operand

13;0010000 /mov
13;0110000 /movb
13;0020000 /cmp
13;0120000 /cmpb
13;0030000 /bit
13;0130000 /bitb
13;0040000 /bic
13;0140000 /bicb
13;0050000 /bis
13;0150000 /bisb
13;0060000 /add
13;0160000 /sub

/ branch

06;0000400 /br
06;0001000 /bne
06;0001400 /beq
06;0002000 /bge
06;0002400 /blt
06;0003000 /bgt
06;0003400 /ble
06;0100000 /bpl
06;0100400 /bmi
06;0101000 /bhi
06;0101400 /blos
06;0102000 /bvc
06;0102400 /bvs
06;0103000 /bhis
06;0103000 /bec
06;0103000 /bcc
06;0103400 /blo
06;0103400 /bcs
06;0103400 /bes

/ jump/ branch type

35;0000400 /jbr
36;0001000 /jne
36;0001400 /jeq
36;0002000 /jge
36;0002400 /jlt
36;0003000 /jgt
36;0003400 /jle
36;0100000 /jpl
36;0100400 /jmi
36;0101000 /jhi
36;0101400 /jlos
36;0102000 /jvc
36;0102400 /jvs
36;0103000 /jhis
36;0103000 /jec
36;0103000 /jcc
36;0103400 /jlo
36;0103400 /jcs
36;0103400 /jes

/ single operand

15;0005000 /clr
15;0105000 /clrb
15;0005100 /com
15;0105100 /comb
15;0005200 /inc
15;0105200 /incb
15;0005300 /dec
15;0105300 /decb
15;0005400 /neg
15;0105400 /negb
15;0005500 /adc
15;0105500 /adcb
15;0005600 /sbc
15;0105600 /sbcb
15;0005700 /tst
15;0105700 /tstb
15;0006000 /ror
15;0106000 /rorb
15;0006100 /rol
15;0106100 /rolb
15;0006200 /asr
15;0106200 /asrb
15;0006300 /asl
15;0106300 /aslb
15;0000100 /jmp
15;0000300 /swab

/ jsr

07;0004000 /jsr

/ rts

10;000200 /rts

/ simple operand

11;104400 /sys

/ flag-setting

01;0000241 /clc
01;0000242 /clv
01;0000244 /clz
01;0000250 /cln
01;0000261 /sec
01;0000262 /sev
01;0000264 /sez
01;0000270 /sen

/ floating point ops

01;170000 / cfcc
01;170001 / setf
01;170011 / setd
01;170002 / seti
01;170012 / setl
15;170400 / clrf
15;170700 / negf
15;170600 / absf
15;170500 / tstf
12;172400 / movf
14;177000 / movif
05;175400 / movfi
14;177400 / movof
05;176000 / movfo
14;172000 / addf
14;173000 / subf
14;171000 / mulf
14;174400 / divf
14;173400 / cmpf
14;171400 / modf
14;176400 / movie
05;175000 / movei
15;170100 / ldfps
15;170200 / stfps
24;000000 / fr0
24;000001 / fr1
24;000002 / fr2
24;000003 / fr3
24;000004 / fr4
24;000005 / fr5

/ 11/45 operations

30;072000 /als (ash)
30;073000 /alsc (ashc)
30;070000 /mpy
.if eae-1
30;070000/ mul
30;071000 / div
30;072000 / ash
30;073000 /ashc
.endif
30;071000 /dvd
07;074000 /xor
15;006700 /sxt
11;006400 /mark
31;077000 /sob

/ specials

16;000000 /.byte
20;000000 /.even
21;000000 /.if
22;000000 /.endif
23;000000 /.globl
25;000000 /.text
26;000000 /.data
27;000000 /.bss
32;000000 /.comm

start:
	cmp	(sp),$4
	bge	1f
	jmp	aexit
1:
	cmp	(sp)+,$5
	blt	1f
	mov	$40,defund		/ globalize all undefineds
1:
	tst	(sp)+
	mov	(sp)+,a.tmp1
	mov	(sp)+,a.tmp2
	mov	(sp)+,a.tmp3
	jsr	r5,ofile; a.tmp1
	movb	r0,txtfil
	jsr	r5,ofile; a.tmp2
	movb	r0,fbfil
	jsr	r5,ofile; a.tmp3
	movb	r0,symf
	movb	r0,fin
	sys	creat; a.out; 0
	bec	1f
	jsr	r5,filerr; a.outp
1:
	movb	r0,fout
	jmp	go

/ overlaid buffer
inbuf	= start
.	= inbuf+512.
