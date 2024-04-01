# Metadata extraction

This page describes how metadata will be extracted from the traces.

## Goal

Based on the four transaction traces (2 normal, 2 reverse order), we automatically determine several labels and metadata related to TOD.

!!! danger

    This does not detect if the amount of a Selfedestruct changed, as this is directly taken from the state and not stored in the stack or memory. Are there other TODs that are not visible in traces?

## Traces preprocessing

### Traces input

As inputs we take the execution traces from the transactions. These are based on the non-finalized [EIP-3155](https://eips.ethereum.org/EIPS/eip-3155) EVM trace specification.

!!! note

    We require the "pc", "op", "stack" and "depth" fields. For deeper analysis, the "memory" field should also be present, eg to identify the CALL input.

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
  "depth": 2,
  "returnData": "0x",
  "refund": "0x0",
  "memSize": "96",
  "opName": "SLOAD"
}
```

### Map each JSON to a `TraceEvent`

This step simply maps a trace event from JSON to a python class (`TraceEvent`).

Currently this is only implemented for traces generated with REVM (based on EIP-3155). However, new implementations could map other traces formats to `TraceEvent`, as long as the necessary information is included in the trace.

### Parse `Instruction`s

Here, we parse the instructions and keep track in which contract they were executed.

We start the process with an initial `CallFrame`, which stores who created the transaction and which contract/EOA is called.

Then we iterate through the `TraceEvent`s, always looking at two successive `TraceEvent`s. Based on these events we create an `Instruction` object, which specifies the EVM instruction, its inputs and also its outputs. For some instructions the call context is important, so we link the current `CallFrame` to the instruction. For instance, an `SLOAD` instruction loads the data from the current contracts storage.

If we encounter a call instruction (`CALL`, `STATICCALL`, `CALLCODE` or `DELEGATECALL`) we create a new `CallFrame`. On a `STOP`, `RETURN`, `REVERT` or `SELFDESTRUCT` we mark the current one as reverted and go back to the previous `CallFrame`. If the depth of the next event is one lower than the current one, we assume an exceptional halt and also revert the current transaction. If the depth of the next event is unexpected, we throw an `UnexpectedDepthChange` Exception.

The `Instruction` includes:

- opcode
- program_counter
- call_frame
- stack_inputs
- stack_outputs
- memory_input
- memory_output
- [additional fields based on the instruction type, eg `key` for `SLOAD`]

!!! warning

    How should we treat inputs/outputs from/to non-stack? in particular, the memory for eg calls?


## Analysis

The analyzers are built in a way, that they don't need access to the whole trace at once. This way, we do not need to load the whole trace into memory at the same time, but instead iterate through the events and analyze them on the go. This is mainly a memory improvement.

### Instruction effect changes

To understand, where the TOD occurs we compare the transaction trace from the normal and attack executions. At each iteration, we compare the `TraceEvent`s, including the program counter, the call depth and the stack. The first time they differ, is the point at which the previous instruction had a different effect.

For instance, if the storage is different for both executions, the `SLOAD` will output a different result to the stack. We report the instruction that was executed before (and caused) the traces diverge, in this case before the stacks diverge.

**Requires**:

- comparison of two traces
- access to next `TraceEvent`s
- access to `Instruction`s

**Labels**:

- TOD-source-instruction

!!! warning

    Check if this also works for reverts.

!!! note

    There could be multiple instructions that are directly affected by the previous transaction, however for all but the first instruction, it is hard to differentiate between a direct effect of the previous transaction, or an indirect effect through the first divergent instruction.

### Instruction input changes

To understand, which instructions are affected by the TOD, we compare if the same instructions were executed, and if they were given the same inputs.

For each instruction we count how often it has been exected in each trace. We identify the instruction by the code_address, pc, opcode and inputs. For instructions in trace A, we increment the counter. For instructions in the other trace, decrement it. Thus, if the instruction occurs in both traces, the count will balance to 0. If the inputs differ, we will have two different elements, one with a +1 count and one with -1.

At the end, we group the instructions only by code_address, pc and opcode, so instructions with different inputs will be grouped together. These are matched between the traces to identify which parameters have changed and outputted as such. If no match exists, we output them as only being executed by one trace.

**Requires**:

- comparison of two traces
- access to `Instruction`s

**Labels**:

- TOD-Amount, TOD-Recipient, TOD-Selfdestruct, (TOD-Transfer also uses `CALL`)
- ether profits
- list of affected instructions

If this includes inputs from the memory, further:

- call input changes
- log changes
- token profits (through log changes)

### Instruction usage

We record all executed unique instructions, eg to understand if hashing was used. We group this by the contract address that executed them.

**Requires**:

- access to `Instruction`s
- access to `CallFrame`s

**Labels**:

- cryptography usage (hashing, signatures)
- usage of recently introduce opcodes

!!! warning

    Solidity uses `keccak256` internally for mappings. Some detection tools based on the source code may understand Solidity mappings, but not usage of `keccak256` in other cases.

## Not yet covered

- usage of precompiled contracts (see [https://www.evm.codes/precompiled](https://www.evm.codes/precompiled))
- attacker-preconditions (eg. if the address from the attacker was returned from a SLOAD or a SLOAD with the attackers address as index returned != 0? Hard to understand without information flow analysis)
- control flow differences (where and through what? implement eg with changes or by comparing instructions)
- attack symmetry (if the order was different, would the "victim" be an "attacker"?)
- output differences (particularly useful, if we group by instruction+inputs => sampe input that yields different output is probably TOD affected)
