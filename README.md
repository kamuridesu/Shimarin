# Shimarin

Asynchronous event-based communication between client and server.


# How to use

Examples are in example folder


# RESTful interface

In order to communicate, this lib uses REST requests.
To fetch events, the client sends a GET request to the route /events?fetch=n, where fetch is the number of events to fetch. The response is a json array containing a number of events less than or equals the fetch number. For example, /events?fetch=5 fetch the first 5 events.

The callback route is defined by /callback and receives a POST request with a header "X-Identifier" containing the event uuid. The body of the request contains data to be used by a user-defined callback function.

You can also setup middlewares for data persistence. See the implementation for SQLite Persistent Middleware.

If you want to use the Flask plugin, just import ShimaApp. It is an instance of a Flask Blueprint so you can just register it in your Flask App.

# Install

```
pip install Shimarin
of 
pip install Shimarin[flask]
```

# Known bugs

- Return type for event trigger is Any because when fetching events it returns `Event[Unknown]` and I could not cast the return type of the callback function to the fetched event. You can always annotate the handler function to retuen the right type. Right now the return type for the Event is Any.

<p align="center">
<img src="https://count.kamuridesu.com?username=shimarin" alt="count"/>
</p>
