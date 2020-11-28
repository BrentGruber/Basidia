# Basidia
Async reimplementation of [nameko](https://github.com/nameko/nameko).  First implementation will be built on AMQP with rabbitmq, however eventually the goal would be to support other broker types such as [nats.io](https://nats.io) or [kafka](https://kafka.apache.org/). HTTP endpoints will not be implemented in Basidia initially and the recommendation will be to create an API Gateway using a framework such as [fastapi](https://github.com/tiangolo/fastapi).  This could change in the future however.

## Goals

The goals for this project are to take the ideas presented by nameko and implement them with more modern technologies with async support and type hinting

1. High Performance
2. Easy to learn
3. Easy to deploy
4. Easy to test
5. Modular
6. Highly Extensible


## Features

* RPC and Events (pub-sub)
* CLI for easy and rapid development
* Utilities for unit and integration testing
* Extensible

## Getting Started

An example hello world micro service
```python
# Helloworld.py

class GreetingService:
    name = "greeting_service"

    @rpc
    async def hello(self, name):
        return f"Hello, {}!"
```

Running it from a shell:

```bash
$ basidia run Helloworld
starting services: greeting_service
```

And using the CLI to start the basidia shell and interact:
```bash
$ basidia shell
>>> b.rpc.greeting_service.hell(name="Brent")
'Hello, Brent!'
```

## Support

## Contribute

* Fork the repository
* Raise an issue or make a feature request

## License

Apache 2.0. See LICENSE for details