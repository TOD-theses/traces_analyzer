# Parsing

## Traces input

As inputs we take the execution traces from the transactions. These are based on the non-finalized [EIP-3155](https://eips.ethereum.org/EIPS/eip-3155) EVM trace specification.

!!! note

    We require the "pc", "op", "stack" and "depth" fields. For better instruction input and output analysis, the "memory" field should also be present, eg to identify the CALL and LOG inputs.

Here is an example trace for an SLOAD instruction:

```json
{
  "pc": 1157,
  "op": 84,
  "gas": "0x1f7b1",
  "gasCost": "0x834",
  "stack": [
    "0xd0e30db0",
    "...",
    "0xd7a8b5b72b22ea76954784721def9efafa7df99d65b759e7d1b78f9ee0094fbc"
  ],
  "memory": "0x00..080",
  "depth": 2,
  "returnData": "0x",
  "refund": "0x0",
  "memSize": "96",
  "opName": "SLOAD"
}
```

## Map each JSON to a `TraceEvent`

This step simply maps a trace event from JSON to a python class (`TraceEvent`).

Currently this is only implemented for traces generated with REVM (based on EIP-3155). However, new implementations could map other traces formats to `TraceEvent`, as long as the necessary information is included in the trace.

## Parse `Instruction`s and the `CallTree`

Here, we parse the instructions and keep track in which contract they were executed.

We start the process with an initial `CallFrame`, which stores who created the transaction and which contract/EOA is called.

Then we iterate through the `TraceEvent`s, always looking at two successive `TraceEvent`s. Based on these events we create an `Instruction` object, which specifies the EVM instruction, its inputs and also its outputs. For some instructions the call context is important, so we link the current `CallFrame` to the instruction. For instance, an `SLOAD` instruction loads the data from the current contracts storage.

If we encounter a call instruction (`CALL`, `STATICCALL`, `CALLCODE`, `DELEGATECALL`, `CREATE` or `CREATE2`) we create a new `CallFrame`. On a `STOP`, `RETURN`, `REVERT` or `SELFDESTRUCT` we mark the current one as reverted and go back to the previous `CallFrame`. If the depth of the next event is one lower than the current one, we assume an exceptional halt and also revert the current transaction. If the depth of the next event is unexpected, we throw an `UnexpectedDepthChange` Exception.

The `Instruction` includes:

- opcode
- name (mnemonic for opcode)
- program_counter
- call_frame
- stack_inputs
- stack_outputs
- memory_input
- memory_output
- data (additional fields based on the instruction type, eg `key` for `SLOAD`)
