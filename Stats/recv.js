'use strict'

process.on('multipleResolves', () => {
    console.error('process.multipleResolves', arguments)
    stop()
})
process.on('rejectionHandled', () => {
    console.error('process.rejectionHandled', arguments)
    stop()
})
process.on('uncaughtException', () => {
    console.error('process.uncaughtException', arguments)
    stop()
})
process.on('unhandledRejection', () => {
    console.error('process.unhandledRejection', arguments)
    stop()
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

    sock.on('timeout', stop)
    sock.on('end', stop)
    sock.on('error', stop)
    sock.on('close', stop)
}

var stop = () => {
    try {
        sock.removeAllListeners()
    } catch(Exception) {
    }
    try {
        sock.destroy()
    } catch(Exception) {
    }

        sock = null

    console.error('Disconnected')
}

process.on('beforeExit', () => {
    setTimeout(start, 500)
})