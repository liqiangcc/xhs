'use strict';

function assertPort(port, name, requiredMethods) {
    if (!port || (typeof port !== 'object' && typeof port !== 'function')) {
        throw new Error(`${name} is required`);
    }
    for (const method of requiredMethods) {
        if (typeof port[method] !== 'function') {
            throw new Error(`${name}.${method}() is required`);
        }
    }
    return port;
}

module.exports = {
    assertPort,
};
