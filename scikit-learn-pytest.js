const { opendir } = require('node:fs/promises');
const { loadPyodide } = require("pyodide");

async function main() {
  let exit_code = 0;
  try {
    global.pyodide = await loadPyodide();
    let pyodide = global.pyodide;
    const FS = pyodide.FS;
    const NODEFS = FS.filesystems.NODEFS;

    let mountDir = "/mnt";
    pyodide.FS.mkdir(mountDir);
    pyodide.FS.mount(pyodide.FS.filesystems.NODEFS, { root: "." }, mountDir);


    await pyodide.loadPackage(["micropip"]);
    // Install previously built scikit-learn wheel
    // await pyodide.runPythonAsync(`
    //     import glob
    //     import micropip

    //     wheel_list = glob.glob('/mnt/dist/*.whl')
    //     emfs_wheel_list = [f"emfs:{each}" for each in wheel_list]
    //     print(f"Installing wheels: {emfs_wheel_list}")
    //     await micropip.install(emfs_wheel_list)

    //     pkg_list = micropip.list()
    //     print(pkg_list)
    // `);
    await pyodide.loadPackage(["micropip"]);
    await pyodide.runPythonAsync(`
       import micropip

       await micropip.install(['scikit-learn'])

       pkg_list = micropip.list()
       print(pkg_list)
    `);

    // Pyodide is built without OpenMP, need to set environment variable to
    // skip related test
    await pyodide.runPythonAsync(`
        import os
        os.environ['SKLEARN_SKIP_OPENMP_TEST'] = 'true'
    `);

    await pyodide.runPythonAsync("import micropip; micropip.install('pytest')");
    // somehow this import is needed not sure why import pytest is not enough...
    await pyodide.runPythonAsync("micropip.install('tomli')");
    let pytest = pyodide.pyimport("pytest");
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

