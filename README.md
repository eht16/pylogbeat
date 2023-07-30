PyLogBeat
=========

[![CI Tests](https://github.com/eht16/pylogbeat/actions/workflows/tests.yml/badge.svg)](https://github.com/eht16/pylogbeat/actions/workflows/tests.yml)
[![PyPI](https://img.shields.io/pypi/v/pylogbeat.svg)](https://pypi.org/project/pylogbeat/)
[![Python Versions](https://img.shields.io/pypi/pyversions/pylogbeat.svg)](https://pypi.org/project/pylogbeat/)
[![License](https://img.shields.io/pypi/l/pylogbeat.svg)](https://pypi.org/project/pylogbeat/)

PyLogBeat is a simple, incomplete implementation of the Beats protocol
used by Elastic Beats and Logstash. For more information about Beats see
https://www.elastic.co/products/beats and
https://www.elastic.co/guide/en/logstash/current/plugins-inputs-beats.html.

With this library it is possible to send log messages or any data to
Logstash' beats input plugin or any other service which implements
the Beats protocol.

The main difference to other transport mechanisms like direct TCP
or UDP transfer is that with the Beats protocol there is a higher
reliability of the data transfer, especially since the server
acknowledges the data it received so the client knows whether and
what to resend.


Installation
------------

The easiest method is to install directly from pypi using pip:

    pip install pylogbeat


If you prefer, you can download PyLogBeat from
https://github.com/eht16/pylogbeat and install it directly from source:

    python setup.py install


Due to a bug (<https://github.com/logstash-plugins/logstash-input-beats/pull/342>)
in some Logstash versions, you will need Logstash >= 5.6.12 or Logstash >= 6.4.0.


Get the Source
--------------

The source code is available at https://github.com/eht16/pylogbeat/.


Usage
-----

### Simple use

```python
    message = {'@timestamp': '2018-01-02T01:02:03',  '@version': '1', 'message': 'hello world'}
    client = PyLogBeatClient('localhost', 5959, ssl_enable=False)
    client.connect()
    client.send([message])
    client.close()
```

### Using a context manager

```python
    with PyLogBeatClient('localhost', 5959, ssl_enable=False) as client:
        client.send([message])
```

### Using a SSL connection

```python
    with PyLogBeatClient('localhost', 5959, ssl_enable=True, ssl_verify=True,
            keyfile='certificate.key', certfile='certificate.crt', ca_certs='ca.crt') as client:
        client.send([message])
```

For details regarding the SSL certificates and how to configure the
Logstash input for SSL, see
https://www.elastic.co/guide/en/logstash/current/plugins-inputs-beats.html.


Message Format
--------------

`PyLogBeatClient.send()` accepts a sequence (list, tuple, set) of "messages".
The messages itself can either be a `dict` object representing the final
message to be sent to Logstash or a `bytes` or `string` object which must
contain properly formatted `JSON`.
If a `dict` is passed as element, it is converted to `JSON` using
`json.dumps()`.

### Example message

The following example is a message as `JSON`:

```python
    {
        "@timestamp": "2018-01-02T01:02:03",
        "@version": "1",
        "extra": {
            "application": "django_example",
            "django_version": "2.1.0",
            "environment": "production"
        },
        "host": "my-local-host",
        "level": "INFO",
        "logsource": "my-local-host",
        "message": "foo bar",
        "pid": 65534,
        "program": "example.py",
        "type": "python-logstash"
    }
```

This is the standard Logstash message format in JSON.


Logging
-------

PyLogBeat uses a logger named "pylogbeat" to log some debug messages
and warnings in case of errors. By default, the logger's log level
is set to `Warning` so you will not see any debug log messages.
If necessary simply change the log level of the logger to see the debug
messages. For example:

```python
    import logging
    logging.getLogger('pylogbeat').setLevel(logging.DEBUG)
```

It is important to make this change *after* you imported
the `pylogbeat` module.

Furthermore, PyLogBeatClient's constructor method takes a `use_logging`
argument which should be a boolean indicating whether the logging
subsystem should be used at all. The argument defaults to `False`,
i.e. if you want any logging, you need to pass `True`.
If PyLogBeat is used itself as part of the logging system (e.g.
as the transport of a handler), it is important to not emit any new
log messages once the logging subsystem has been shutdown or is in the
process of shutting down. In this case, `use_logging` must be `False`
in order to suppress generating log messages.


Protocol Support
----------------

The implemented Beats protocol is not yet officially specified and
documented, unfortunately. Hopefully the Beats developers will
provide a specification in the future.
So far, sending the data and waiting for the ACK from the server is
implemented. But there might some details from the protocol missing
in the implementation.


Future Maintenance
------------------

If you are interested in the code, want to improve it and/or
complete the protocol support, please feel free to send PRs.
I would be happy if someone likes to continue developing this library
and would also take full maintainership for future development and
releases.


Contributing
------------

Found a bug or got a feature request? Please report it at
https://github.com/eht16/pylogbeat/issues.


Credits
-------

This code is based on https://github.com/brxie/PyLumberjack and
adopted to support version 2 of the protocol.
Thanks to brxie for the initial code.


ChangeLog
---------

### 2.0.1 / 2023-07-30

- Load certificate chain only if a certificate was specified


### 2.0.0 / 2020-10-04

- Remove "six" dependency
- Require Python >= 3.6


### 1.0.5 / 2020-10-04

- Set `python_requires` to Python >=2.7 or Python >= 3.6 for
  smooth upgrade to upcoming Python3 only.
  This way Python2 only users will stay at this release.


### 1.0.4 / 2020-05-06

- Validate input data and fix documentation about accepted values (#2)


### 1.0.3 / 2020-04-22

- Add note about required Logstash versions (#1)
- Improve unit tests


### 1.0.2 / 2018-12-31

- Add badges to README


### 1.0.1 / 2018-12-31

- Fix typo in setup.py
- Use distribution "trusty" for Travis builds


### 1.0.0 / 2018-12-31

- Initial release


License
-------
PyLogBeat is licensed under the Apache License 2.0.


Author
------

Enrico Tröger <enrico.troeger@uvena.de>
