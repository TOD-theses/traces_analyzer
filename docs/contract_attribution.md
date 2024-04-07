# Contract attribution

Here, we describe how to attribute a label to specific contracts of the trace.

## TOD definitions

- write-write conflict: use the contract from the SSTORE instruction
- write-read conflict: use the contract from the SLOAD/... instruction
- instruction changes: use the contracts from all instructions between the SLOAD/... instruction and the CALL/... instruction

### Alternative ideas

If the `SLOAD` is within a contract and the sink (call/log change) is in the parent contract, we would currently take both contracts. We could also only take the parent contract and say that the `CALL` was the problem, yielding a different output and taking it as a source (ignoring the inner workings of the CALL). However, the other way around, this does not work (An `SLOAD` is in the parent and the `LOG` is in the child).