# Feature extraction

This page describes how features will be extracted from trace pairs.

## Instruction effect changes

To understand, where the TOD occurs we compare the transaction trace from the normal and attack executions. At each iteration, we compare the `Instruction`s and stop as soon as we find the TOD source.

If two instructions have a different output (eg an `SLOAD` that loads a different value from storage), we consider them to be the TOD source.

If this did not happen yet, but two instructions differ otherwise (inputs, program counter, etc), we take the previous instructions as TOD source. For example, this can happen if a `CALL` occurs and in one trace there is enough balance to do this, while the other trace has insufficient balance to do so.

**Requires**:

- comparison of two traces
- access to `Instruction`s

**Labels**:

- TOD-source-instruction

!!! warning

    Check if this also works for reverts.

!!! note

    There could be multiple instructions that are directly affected by the previous transaction, however for all but the first instruction, it is hard to differentiate between a direct effect of the previous transaction, or an indirect effect through the first divergent instruction.

## Instruction changes

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

## Instruction usages

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

## Taint Flow analysis

We could also do taint flow analysis with a few modifications. If we replace the string values on the stack, memory and calldata with objects that store `(value, written_by: Instruction and read_by: list[Instruction])`, then we would know which write did affect which reads and thus which instructions influenced which following instructions.

This could be used for:
- checking if the attackers address was used for some check (if conditions) or influenced the sink (both, directly or through sstore->sload/tstore->tload/...)
- to reduce the number of vulnerable accounts in one source->sink flow (if we know the flow we know exactly which contracts are involved, instead of relying on heuristics that potentially include too many)