const { packager } = require('@electron/packager');
packager({dir:'.',name:'Applicatron3000',platform:'win32',arch:'x64',out:'build',overwrite:true,asar:true,extraResource:['build/mail-runtime'],ignore:[/^\/(tests|docs|build|\.git|\.github|\.openai)(\/|$)/]}).then(console.log).catch(e=>{console.error(e);process.exitCode=1});
