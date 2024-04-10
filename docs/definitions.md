# TOD definitions

Here we will show several definitions of TOD. Sub-headers are used to indicate, that the definition is a specialization of the upper definition.

!!! note

    We could differ between definitions that are focused on the outcome (taking the execution as a black-box) and definitions that are focused on the execution (ignoring the resulting state). eg "differences in the resulting balances" vs "differences in the execution's ether flows".

[TOC]

## World State

A TOD occurs, when executing transactions in a different order yields different world states.

The world state is a mapping from addresses to account states, and the account state includes:

- nonce
- balance
- storageRoot
- codeHash

Thus, two transactions are TOD, iff the balance, the storage or the code of an account, or the nonce of a smart contract is dependent on the transaction order (the nonce of an EOA cannot be influenced by the transactions).

### Write-Write conflict

A TOD occurs, when both transactions overwrite different values to the same storage location.

An example of this is ERC-20 approve, where both transactions write to `approved[victim][attacker]`. The remaining amount of approved tokens is the write-value of the second transaction.

!!! note

    Only for storage there is a relevant overwrite functionality. For balances, there is only a set-to-0 functionality with `selfdestruct`. For `CREATE2` it is theoretically possible if there is also a Write-Read conflict (so the initialisation_code can fetch different data, depending on which transaction got executed first). For `CREATE`, the two creations will use different nonces and thus have different destinations.

### Write-Read

A TOD occurs, when the first transactions modifies a value and the second transaction reads this value. The value could be stored in the storage or be an accounts balance. to the storage and the second transaction reads this value from the storage.

!!! warning

    This definition also includes the case, where `selfdestruct(recipient)` writes and reads the balance. This would need special care in the implementation.

!!! note

    This definition does not necessarily imply a world state change. For instance, assume a `counter` currently has a value `0`. The first transaction increments it to `1`. The second transaction makes an `if (counter > 2)`. There is a write-read conflict, however this does not affect the world state (neither in storage, logs, code, gas, etc.).

#### Call changes

A TOD occurs, if the existence of a call instruction, or its stack and memory inputs, depend on the transaction order.

Type of calls: CALL, STATICCALL, 

!!! note

    Should we include selfdestruct here?

##### Ether flow changes

A TOD occurs, if the sending of ether (source, recipient or amount) depends on the transaction order.

#### Log changes

A TOD occurs, if the existence of a log instruction, or its stack and memory inputs, depend on the transaction order.

##### Token flow changes

A TOD occurs, if the sending of tokens (source, recipient or amount) depends on the transaction order.
