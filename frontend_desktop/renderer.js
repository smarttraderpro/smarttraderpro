// renderer.js (Electron Renderer Process)

// This file is loaded by the index.html file and will
// be executed in the renderer process for that window.
// All Node.js APIs are not available in this process when
// contextIsolation is true and nodeIntegration is false.
// Use preload.js to selectively expose Node.js features
// to the renderer process.

console.log('Renderer process script loaded.');

// Example: You can add DOM manipulation or UI logic here.
// document.addEventListener('DOMContentLoaded', () => {
//   const replaceText = (selector, text) => {
//     const element = document.getElementById(selector);
//     if (element) element.innerText = text;
//   };

//   replaceText('app-version', navigator.userAgent); // Example
// });

// If using preload.js, you might interact with exposed APIs like this:
// window.myAPI.doSomething();
