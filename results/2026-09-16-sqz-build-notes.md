# sqz Mac build bring-up — failed attempts retained

Before successful run 35130900071, four bounded controller attempts failed before model inference and are retained as setup failures rather than hidden:

1. Homebrew `cargo/rustc` aborted due a Homebrew Rust/LLVM dylib symbol mismatch.
2. Preferring `$HOME/.cargo/bin` still resolved the broken Homebrew rustc path.
3. A disposable Rust 1.90.0 install succeeded, but `cargo +1.90.0` was invoked through a non-rustup cargo binary and failed before compilation.
4. `rustup run 1.90.0 cargo` still inherited the broken external rustc selection.

Final repair used a disposable `RUSTUP_HOME`/`CARGO_HOME`, installed Rust 1.90.0 there, then invoked the exact toolchain `cargo` and set `RUSTC` to the exact isolated toolchain rustc. The upstream quality benchmark and release build then passed. No model calls were made by failed build attempts and no global Rust installation/configuration was changed.
