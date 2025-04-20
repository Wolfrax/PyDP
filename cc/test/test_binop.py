from test.compiler_fixture import *

def test_basic_binop(CCompiler):
    src_code = (
        ("main() { i = 1 + 2; }", 3),
    )

    for src in src_code:
        result, ext_decl = CCompiler.compile(src[0])
        assert result is None
        for ind, ed in enumerate(ext_decl):
            size = ed.struct_size if 'struct_specifier' in ed.ctx else ed.size
            print(f"size = {size}")
            assert size == src[ind + 1]

