from py2many.pyrs.transpiler import RustTranspiler


def test_dotted_import_from_adds_only_root_crate_to_externs():
    transpiler = RustTranspiler()

    import_line = transpiler._import_from(
        "calibre.customize", ["InterfaceActionBase"]
    )
    usings = transpiler.usings()

    assert import_line == "use calibre::customize::{InterfaceActionBase};"
    assert "extern crate calibre;" in usings
    assert "extern crate calibre.customize;" not in usings


def test_dotted_import_adds_rust_module_path_and_root_crate():
    transpiler = RustTranspiler()

    transpiler._import("PyQt5.Qt")
    usings = transpiler.usings()

    assert "extern crate PyQt5;" in usings
    assert "extern crate PyQt5.Qt;" not in usings
    assert "use PyQt5::Qt;" in usings
