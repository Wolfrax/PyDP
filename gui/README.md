This GUI is using javascript frameworks **React** and **Vite**.

Node needs to be installed, see [Node](https://nodejs.org/en/download/package-manager) how to do this.
As described
```bash
# installs nvm (Node Version Manager)
$ curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.0/install.sh | bash

# download and install Node.js (you may need to restart the terminal)
$ nvm install 22

# verifies the right Node.js version is in the environment
$ node -v # should print `v22.6.0`

# verifies the right npm version is in the environment
$ npm -v # should print `10.8.2`
```

In case Node is already installed but needs to be updated try these steps (from [freeCodeCamp](https://www.freecodecamp.org/news/how-to-update-node-and-npm-to-the-latest-version/))

```bash
$ sudo npm install -g n
$ sudo n lts # long term support version
$ sudo n latest
$ sudo n prune # Remove old versions
```

Install Node packages (from package-lock.json)
```bash
$ npm install
```
Now vite should be installed

```bash
# -D will install vite in devDependencies only, see 
# https://stackoverflow.com/questions/23177336/what-does-npm-d-flag-mean 
$ npm install -D vite
```

Now start `asm_api_server.py` (in the asm-directory), then - in a terminal window do

```bash
$ npm run dev # or $ npx vite
```

Then press o-key to open the browser, the debug console for the assembler should be visible.

Above is automated in `start.bash`-script (starting the api server and vite), `$ sh start.bash`

Vite consists of two major parts:

* The dev server provides support for Hot Module Replacement (HMR) for updating modules during the execution of the application. 
When changes are made to the source code of an application, only the changes are updated, rather than the entire application being reloaded. 
This feature helps speed up development time.
* The build command enables developers to bundle their code with Rollup, pre-configured to output highly 
optimized static assets for production.vite supports modularization of javascript code and dynamic loading of changed code

