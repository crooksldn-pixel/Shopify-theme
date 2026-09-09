"""The general read layer: a bounded, typed query over the store's recent orders, answered
from a cache the Mac keeps warm, so a question about best sellers, sales by size, customers
worth the most or stock about to run out is one query rather than a tool written for it.

Read-only by construction: nothing in this package can send a mutation. Every write remains
a named, reviewed, staged change on the action engine."""
