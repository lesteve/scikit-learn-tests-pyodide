const { opendir } = require('node:fs/promises');
const { loadPyodide } = require("pyodide");

// From https://github.com/numpy/numpy/pull/21895
function make_tty_ops(stream){
  return {
    // get_char has 3 particular return values:
    // a.) the next character represented as an integer
    // b.) undefined to signal that no data is currently available
    // c.) null to signal an EOF
    get_char(tty) {
      if (!tty.input.length) {
        var result = null;
        var BUFSIZE = 256;
        var buf = Buffer.alloc(BUFSIZE);
        var bytesRead = fs.readSync(process.stdin.fd, buf, 0, BUFSIZE, -1);
        if (bytesRead === 0) {
          return null;
        }
        result = buf.slice(0, bytesRead);
        tty.input = Array.from(result);
      }
      return tty.input.shift();
    },
    put_char(tty, val) {
      try {
        if(val !== null){
          tty.output.push(val);
        }
        if (val === null || val === 10) {
          process.stdout.write(Buffer.from(tty.output));
          tty.output = [];
        }
      } catch(e){
        console.warn(e);
      }
    },
    flush(tty) {
      if (!tty.output || tty.output.length === 0) {
        return;
      }
      stream.write(Buffer.from(tty.output));
      tty.output = [];
    }
  };
}

// From https://github.com/numpy/numpy/pull/21895
function setupStreams(FS, TTY){
  let mytty = FS.makedev(FS.createDevice.major++, 0);
  let myttyerr = FS.makedev(FS.createDevice.major++, 0);
  TTY.register(mytty, make_tty_ops(process.stdout))
  TTY.register(myttyerr, make_tty_ops(process.stderr))
  FS.mkdev('/dev/mytty', mytty);
  FS.mkdev('/dev/myttyerr', myttyerr);
  FS.unlink('/dev/stdin');
  FS.unlink('/dev/stdout');
  FS.unlink('/dev/stderr');
  FS.symlink('/dev/mytty', '/dev/stdin');
  FS.symlink('/dev/mytty', '/dev/stdout');
  FS.symlink('/dev/myttyerr', '/dev/stderr');
  FS.closeStream(0);
  FS.closeStream(1);
  FS.closeStream(2);
  FS.open('/dev/stdin', 0);
  FS.open('/dev/stdout', 1);
  FS.open('/dev/stderr', 1);
}

async function main() {
  let exit_code = 0;
  try {
    global.pyodide = await loadPyodide();
    let pyodide = global.pyodide;
    const FS = pyodide.FS;
    // For now disabling this to avoid causing unknown issues. The pytest
    // output is not as nice but we can live with this
    // setupStreams(FS, pyodide._module.TTY);
    const NODEFS = FS.filesystems.NODEFS;

    let mountDir = "/mnt";
    pyodide.FS.mkdir(mountDir);
    pyodide.FS.mount(pyodide.FS.filesystems.NODEFS, { root: "." }, mountDir);


    await pyodide.loadPackage(["micropip"]);
    // Install previously built scikit-learn wheel
    await pyodide.runPythonAsync(`
        import glob
        import micropip

        wheel_list = glob.glob('/mnt/dist/*.whl')
        emfs_wheel_list = [f"emfs:{each}" for each in wheel_list]
        print(f"Installing wheels: {emfs_wheel_list}")
        await micropip.install(emfs_wheel_list)
    `);

    // Pyodide is built without OpenMP, need to set environment variable to
    // skip related test
    await pyodide.runPythonAsync(`
        import os
        os.environ['SKLEARN_SKIP_OPENMP_TEST'] = 'true'
    `);

    // Needed somehow scikit-learn>=1.2 needs recent joblib and recent joblib
    // needs distutils which is not packaged in Pyodide
    await pyodide.runPythonAsync(`micropip.install('distutils')`);
    await pyodide.runPythonAsync(`import joblib`);
    await pyodide.runPythonAsync(`import sklearn; print(f"scikit-learn version: {sklearn.__version__}")`);

    await pyodide.runPythonAsync("import micropip; micropip.install('pytest')");
    // somehow this import is needed not sure why import pytest is not enough...
    await pyodide.runPythonAsync("micropip.install('tomli')");
    let pytest = await pyodide.runPythonAsync("import pytest; pytest");
    let args = process.argv.slice(2);
    args = ["--pyargs"].concat(args);
    console.log('pytest args:', args);
    exit_code = pytest.main(pyodide.toPy(args));
  } catch (e) {
    console.error(e);
    // Arbitrary exit code here. I have seen this code reached instead of a
    // Pyodide fatal error sometimes (I guess kind of similar to a random
    // Python error). When there is a Pyodide fatal error we don't end up here
    // somehow, and the exit code is 7
    exit_code = 66;

  } finally {
    process.exit(exit_code);
  }
}

main();

