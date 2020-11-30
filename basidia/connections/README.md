The connections directory is for defining required broker connections

Connections require 2 definitions:
1. a function named get_connection that will return a connection object connected to the broker
2. a class named Publisher with an instance method named publish that is able to publish a message to the broker