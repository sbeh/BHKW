'use strict'

;[
    'multipleResolves',
    'rejectionHandled',
    //'uncaughtException',
    'unhandledRejection'
].forEach(event => {
    process.on(event, () => {
        console.log(event, ...arguments)
    })
})

const fs = require('fs')

const config = JSON.parse(fs.readFileSync('config.json'))

var dataFd = null

process.on('beforeExit', () => {
    setTimeout(() => {
        if (dataFd === null)
            open()
        else
            read()
    }, config.parserRetryReadOnEOFAfterMinutes * 60 * 1000)
})

open()

function open() {
    fs.open('data.json', 'r' /*TODO remove on Node.js v11*/, (error, fd) => {
        if (error)
            console.error('Error while opening data.json', error)
        else {
            dataFd = fd
            read()
        }
    })
}


function read() {
    const SIZE = 4096
    fs.read(dataFd, new Uint8Array(SIZE), 0, SIZE, null, (error, bytesRead, buffer) => {
        if (error)
            console.error('Error while reading data.json', error)
            // TODO remove fd? check for values already read and inserted
        else if (bytesRead > 0) {
            parse(buffer.subarray(0, bytesRead))

            if (bytesRead === SIZE)
                read()
        }
    })
}

var unparsed = ''
function parse(buffer) {
    unparsed += String.fromCharCode(...buffer)
    unparsed = unparsed.split('\n').filter(piece => {
        var json
        try {
            json = JSON.parse(piece)
        } catch(SyntaxError) {
            return true
        }

        data(json)
        return false
    }).join('\n')
}

const assert = require('assert')

var regex = JSON.parse(fs.readFileSync('parse_regex.json'))
for(var name in regex)
    regex[name] = new RegExp(regex[name])

var undata
function data(json) {
    if(undata)
        // just add text piece of the message and
        // keep timestamp from first part of message
        undata.data += json.data
    else
        undata = json

    assert(undata.data.length < 300)

    if (!undata.data.includes('\n'))
        // a message is terminated by \n, none of the regex will match
        return
    
    var unmatched = true
    for(var name in regex) {
        var match = regex[name].exec(undata.data)
        if (match) {
            unmatched = false

            if (match.groups)
                // some messages are just commands, dont insert them into database
                insert(undata.time, name, match.groups)
    
            // strip matched text piece from message
            // most of the times, the message string will be empty afterwards
            // but sometimes two messages were send almost at the same time
            undata.data = undata.data.substr(0, match.index) + undata.data.substr(match.index + match[0].length)
            if (undata.data.length === 0) {
                undata = undefined
                break
            }
        }
    }

    if (unmatched) {
        console.error('Could not match data with regex', undata)
        undata = undefined
    }
}

var influx = require('influx')

function insert(time, name, data) {
    var ifdb = connect(name, data)

    if (name === 'P')
        switch(data.P) {
            case 'Hoch': data.P = 1; break
            case 'AUS': data.P = 0; break
            case 'Runter': data.P = -1; break
            default:
                console.error('Unknown value for P', JSON.stringify({time: time, name: name, data: data}))
        }

    for(var field in data)
        switch (data[field]) {
            case 'AN': data[field] = true
            case 'AUS': data[field] = false
        }

//    return

    ifdb.points.push({
        measurement: name,
        fields: data,
        timestamp: new Date(time),
        //tags: {host: 'local'}
    })

    send(ifdb)
}

var influxdb = {}
function connect(name, data) {
    if (!influxdb[name]) {
        var fields = {}
        for(var field in data) {
            if (data[field].includes('.'))
                fields[field] = influx.FieldType.FLOAT
            else
                fields[field] = influx.FieldType.INTEGER
        }
        influxdb[name] = {
            conn: new influx.InfluxDB(Object.assign({}, config.parserInflux/*, {
                schema: [{
                        measurement: name,
                        fields: fields,
                        tags: ['host']
                }]
            }*/)),
            points: [],
            busy: false
        }
    }

    return influxdb[name]
}

function send(ifdb) {
    assert(ifdb.points[0])

    if (ifdb.busy)
        return
    ifdb.busy = true

    var points = ifdb.points
    ifdb.points = []

    ifdb.conn.writePoints(points).then(() => {
        console.error(`Uploaded ${points.length} data points`)
        ifdb.busy = false

        if (ifdb.points[0])
            send(ifdb)
    }).catch(error => {
        console.error('Error uploading date to influx', error)
        ifdb.points.unshift(points)
        ifdb.busy = false
    })
}