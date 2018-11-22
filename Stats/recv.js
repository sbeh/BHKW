'use strict'

;[
    'multipleResolves',
    'rejectionHandled',
    ['uncaughtException', error => stop(`uncaughtException (${error})`)],
    'unhandledRejection'
].forEach(event => {
    if (event instanceof Array)
        process.on(event[0], event[1])
    else
        process.on(event, () => stop(event))
})

var config = JSON.parse(require('fs').readFileSync('config.json'))

var sock

var start = () => {
    sock = require('net').createConnection(config.port, config.host, () => {
        console.error('Connected')

        sock.setEncoding('utf8')
        sock.setKeepAlive(true, 50 * 1000/* 50 seconds */)
        sock.setTimeout(6 * 60 * 1000/* 6 minutes */)
    })

    sock.on('data', data => {
        console.log(JSON.stringify({
            time: Date.now(),
            data: data
        }))
    })

    ;[
        'timeout',
        'end',
        ['error', error => stop('error (' + error.message + ')')],
        ['close', hadError => stop('close' + (hadError ? ' (had error)' : ''))]
    ].forEach(event => {
        if (event instanceof Array)
            sock.on(event[0], event[1])
        else
            sock.on(event, () => stop(event))
    })
}

var stop = (reason) => {
    try {
        sock.removeAllListeners()
    } catch(Exception) {
    }
    try {
        sock.destroy()
    } catch(Exception) {
    }

    sock = null

    console.error('Disconnected', reason)
}

process.on('beforeExit', () => {
    setTimeout(start, 500)
})