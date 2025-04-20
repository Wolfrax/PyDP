from test.compiler_fixture import *

def test_var_decl_size(CCompiler):
    src_code = (
        ("auto v0;", CCompiler.sz('int')),
        ("int v1;", CCompiler.sz('int')),
        ("char v2;", CCompiler.sz('char')),
        ("float v3;", CCompiler.sz('float')),
        ("double v4;", CCompiler.sz('double')),
        ("long v5;", CCompiler.sz('long')),
        ("int *v6;", CCompiler.sz('pointer')),
        ("auto **v7;", CCompiler.sz('pointer')),
        ("int arr1[1];", CCompiler.sz('int') * 1),
        ("int arr2[1+1];", CCompiler.sz('int') * (1+1)),
        ("float arr3[1+7];", CCompiler.sz('float') * (1+7)),
        ("float *arr4[17];", CCompiler.sz('pointer') * 17),
        ("static int arr5[3][5][7];", CCompiler.sz('int') * (3*5*7)),
        ("#define A 9 \n int arr6[A+1];", CCompiler.sz('int') * 10),
        ("int(*c)();", CCompiler.sz('pointer')),
        ("struct s1 {int m1; char m2;} s1;", CCompiler.sz('int') + CCompiler.sz('char')),
        ("struct s2 {int m3; char m4;} s2[10];", (CCompiler.sz('int') + CCompiler.sz('char')) * 10),
        ("struct s3 {int m5; int m6;}; struct s4 {struct s3 m7[5]; int m8;} s3[10];",
         CCompiler.sz('int') + CCompiler.sz('int'),
        (((CCompiler.sz('int') + CCompiler.sz('int')) * 5) + CCompiler.sz('int')) * 10),
        ("struct s3 {int m5[5]; int m6[6];}; struct s4 {struct s3 m7[5]; int m8;} s3[10];",
         CCompiler.sz('int') * 5 + CCompiler.sz('int') * 6,
         (((CCompiler.sz('int') * 5 + CCompiler.sz('int') * 6) * 5) + CCompiler.sz('int')) * 10),
        ("struct s4 { int m9[10]; } s4;", CCompiler.sz('int') * 10),
        ("struct s5 { int m10; } s5;", CCompiler.sz('int')),
        ("struct s6 { int m11[10]; int m12; }; struct s7 { struct s6 m13[10]; int m14; } s7;",
         CCompiler.sz('int') * 10 + CCompiler.sz('int'),
         ((CCompiler.sz('int') * 10 + CCompiler.sz('int')) * 10 + CCompiler.sz('int'))),
        ("struct s6 { int *m11[10]; int m12; }; struct s7 { struct s6 *m13[10]; int m14; } s7[10];",
         CCompiler.sz('pointer') * 10 + CCompiler.sz('int'),
         ((CCompiler.sz('pointer') * 10 + CCompiler.sz('int')) * 10)),
        ("struct s8 { int m15; int m16; }; struct s9 { struct s8 m17; int m18; } s9;",
         CCompiler.sz('int') + CCompiler.sz('int'),
         (CCompiler.sz('int') + CCompiler.sz('int')) + CCompiler.sz('int')),
        ("struct s10 { int m19; int m20; }; struct s11 { struct s10 m21[10]; int m22; } s11;",
         CCompiler.sz('int') + CCompiler.sz('int'),
         (CCompiler.sz('int') + CCompiler.sz('int')) * 10 + CCompiler.sz('int')),
        ("struct s12 { struct s13 { int m23; int m24; } m24; int m25; } s12;",
         CCompiler.sz('int') + CCompiler.sz('int') + CCompiler.sz('int')),
        ("struct s14 { struct s15 { int m26; int m27; } m28[10]; int m29; } s14;",
         (CCompiler.sz('int') + CCompiler.sz('int')) * 10 + CCompiler.sz('int')),
        ("struct s15 { int m30; int m31; }; struct s15 s15;",
         CCompiler.sz('int') + CCompiler.sz('int'), CCompiler.sz('int') + CCompiler.sz('int')),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            size = ed.struct_size if 'struct_specifier' in ed.ctx else ed.size
            print(f"size = {size}")
            assert size == src[ind + 1]

def test_array_decl_elem(CCompiler):
    src_code = (
        ("int arr1[1];", 1),
        ("int arr2[1+1];", (1+1)),
        ("static int arr3[3][5][7];", (3*5*7)),
        ("#define A 9 \n int arr4[A+1];", 10),
        ("int *a[2] { 1, 2 };", 2)
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            print(f"Reading {ed.rank} elements")
            assert ed.rank == src[ind + 1]

def test_var_decl_with_init(CCompiler):
    src_code = (
        ("int v1 123;", 123),
        ("int v2 'a';", ord('a')),
        ("char v3 'a';", 'a'),
        ("char v4 97;", chr(97)),
        ("float v5 3.14;", 3.14),
        ("double v6 4.25;", 4.25),
        ("long v7 321;", 321),
        ("int v9 { 1 + 1 };", 1 + 1),
        ("int v10 { 'a' };", ord('a')),
        ("#define A 123 \n int v11 { A };", 123),
        ("int *v12 1;", 1),
        ("int **v13 1;", 1),
        ('char v14[] "DEF";', "DEF"),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            if 'array' in ed.ctx:
                val = CCompiler.compiler.symbols.memory.read_string(ed.mempos)
            else:
                val = CCompiler.compiler.symbols.memory.read(ed.mempos, ed.type_name)
            if ed.type_name in ['float','double']:
                val = round(val, 2)
            print(f"Reading {val} from memory")
            assert val == src[ind + 1]

def test_var_decl_with_array_init(CCompiler):
    src_code = (
        ("char v15[2] {'a', 'b'}; char *v16 v15;", 'ab', 'a'),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            if 'array' in ed.ctx:
                val = CCompiler.compiler.symbols.memory.read_string(ed.mempos)
            else:
                if ed.pointer:
                    addr = CCompiler.compiler.symbols.memory.read(ed.mempos, 'pointer')
                    val = CCompiler.compiler.symbols.memory.read(addr, ed.type_name)
                else:
                    val = CCompiler.compiler.symbols.memory.read(ed.mempos, ed.type_name)
            if ed.type_name in ['float','double']:
                val = round(val, 2)
            print(f"Reading {val} from memory")
            assert val == src[ind + 1]

def test_indirect_var_decl_with_init(CCompiler):
    src_code = (
        ('char *v2 "ABC";', "ABC"),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            addr = CCompiler.compiler.symbols.memory.read(ed.mempos, 'pointer')
            val = CCompiler.compiler.symbols.memory.read_string(addr)
            print(f"Reading {val} from memory")
            assert val == src[ind + 1]

def test_array_decl_with_init(CCompiler):
    src_code = (
        ("int v1[3] {1, 2, 3};", [1, 2, 3]),
        ("float v2[2] {1, 2.1, 3.2};", [1, 2.1, 3.2]),
        ("long v3[] {3, 2, 1};", [3, 2, 1]),
        ("double v4[] {1.01, 2.02, 3.03};", [1.01, 2.02, 3.03]),
        ('char *v5[] {"abc", "def", 0};', ["abc", "def", ""]),
        ('#define A 1 \n int b; \n int a[] { A, b, 3 };', [1, 0, 3]),
    )
    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        values = []
        for ind, ed in enumerate(ext_decl):
            pos = ed.mempos
            if ed.hasattr('initializer'):
                for ind in ed.initializer:
                    if ed.pointer:
                        addr = CCompiler.compiler.symbols.memory.read(pos, 'pointer')
                        val = CCompiler.compiler.symbols.memory.read_string(addr)
                    else:
                        val = CCompiler.compiler.symbols.memory.read(pos, ed.type_name)
                    if ext_decl[0].type_name in ['float','double']:
                        val = round(val, 2)
                    values += [val]
                    if ed.pointer:
                        pos += CCompiler.sz('pointer')
                    else:
                        pos += CCompiler.sz(ed.type_name)
        print(f"Reading {values} from memory")
        assert values == src[1]

def test_array_decl_with_address(CCompiler):
    src_code = (
        ('int *arr1[1] 1;', [1]),  # Special case, array with 1 element, initialized to address 1
        ("int *arr2[2] { 1, 2 };", [1, 2]),
    )
    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        val = []
        for ind, ed in enumerate(ext_decl):
            mempos = ed.mempos
            for elem in range(ed.rank):
                val += [CCompiler.compiler.symbols.memory.read(mempos, 'pointer')]
                print(f"Reading {val} from memory")
                mempos += CCompiler.sz('pointer')
            assert val == src[ind + 1]

def test_struct_decl_with_init(CCompiler):
    src_code = (
        ("struct t1 { int m1; int m2; } v1 { 1, 2 };", [1, 2]),
        ('struct t2 { char *m3; int m4; } v2 { "abc", 1 };', ["abc", 1]),
        ('struct t3 { char *m5; int m6; }; struct t3 v3 { "abc", 1 };', ["abc", 1], ["abc", 1]),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        members = []
        for ind, ed in enumerate(ext_decl):
            for member in ed.declaration_list:
                if member.pointer:
                    addr = CCompiler.compiler.symbols.memory.read(member.mempos, 'pointer')
                    val = CCompiler.compiler.symbols.memory.read_string(addr)
                else:
                    val = CCompiler.compiler.symbols.memory.read(member.mempos, member.type_name)
                print(f"Reading {val} from memory")
                members += [val]
            assert members == src[ind + 1]

def test_struct_array_decl_with_init(CCompiler):
    src_code = (
        ('struct t1 { char *m1; int m2; } v1[] { "abc", 1, "def", 2 };', ["abc", 1, "def", 2]),
        ('struct t2 { char *m3; int m4; }; struct t2 v2[] { "ghi", 1, "jkl", 2 };', [], ["ghi", 1, "jkl", 2]),
    )

    for src_ind, src in enumerate(src_code):
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        members = []

        struct_var = None
        type_var = None
        for ext in ext_decl:
            if ext.hasattr('mempos'):
                struct_var = ext
            else:
                type_var = ext
        if type_var is None:
            type_var = struct_var

        assert struct_var is not None and type_var is not None

        pos = struct_var.mempos
        for ind in range(struct_var.rank):
            for member in type_var.declaration_list:
                if member.pointer:
                    addr = CCompiler.compiler.symbols.memory.read(pos, 'pointer')
                    members += [CCompiler.compiler.symbols.memory.read_string(addr)]
                else:
                    members += [CCompiler.compiler.symbols.memory.read(pos, member.type_name)]
                pos += member.size
        print(f"Reading {members} from memory")
        assert members == src[src_ind + 1]