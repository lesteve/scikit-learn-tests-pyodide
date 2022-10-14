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
  let exitcode = 0;
  try {
    global.pyodide = await loadPyodide();
    let pyodide = global.pyodide;
    const FS = pyodide.FS;
    setupStreams(FS, pyodide._module.TTY);
    const NODEFS = FS.filesystems.NODEFS;
    await pyodide.runPythonAsync(`
      from pyodide.http import pyfetch
      response = await pyfetch("https://github.com/scikit-learn/scikit-learn/archive/refs/tags/1.1.1.zip")
      await response.unpack_archive() # by default, unpacks to the current dir
    `);

    await pyodide.loadPackage(["micropip"]);
    await pyodide.loadPackage(["scikit-learn"]);
    await pyodide.runPythonAsync(`
      import os
      import shutil
      import glob

      import sklearn

      sklearn_folder = os.path.dirname(sklearn.__file__)

      test_src_folders = glob.glob('scikit-learn/**/tests', recursive=True)

      for src in test_src_folders:
          dst = src.replace('scikit-learn/sklearn', sklearn_folder)
          shutil.copytree(src, dst)

      # sklearn.conftest is needed
      shutil.copy('scikit-learn/sklearn/conftest.py', f'{sklearn_folder}/conftest.py')

    `);
    await pyodide.runPythonAsync("import micropip; micropip.install('pytest')");
    // somehow this import is needed not sure why import pytest is not enough...
    await pyodide.runPythonAsync("micropip.install('tomli')");
    await pyodide.runPythonAsync("import pytest");
    let args = process.argv.slice(2);
    let args_str = args.join(' ');

    let pytest_cmd_str = `pytest.main("--pyargs ${args_str}".split())`;
    console.log('pytest command:', pytest_cmd_str);
      await pyodide.runPythonAsync(pytest_cmd_str);
  } catch (e) {
    console.error(e);
    exitcode = 1;
  } finally {
    // worker.terminate();
    process.exit(exitcode);
  }
}

main();

