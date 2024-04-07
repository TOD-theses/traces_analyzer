# Notes

#### ERC20 Approval



This is a case of a write-write conflict between the two transactions.

#### Explanation

Lets assume, that the victim already approved 100 tokens for the attacker (`approved[victim][attacker] == 100`).

Now, the victim tries to change this to 150 approved tokens instead. However, the attacker notices the transaction in the mempool and quickly withdraws the approved tokens with transferFrom.

Attack scenario:
```
approved[victim][attacker] = 0 (-= 100)   --> Transfer(victim, attacker, 100)
approved[victim][attacker] = 150          --> Approval(victim, attacker, 150)
```

Reverse scenario writes:
```
approved[victim][attacker] = 150          --> Approval(victim, attacker, 150)
approved[victim][attacker] = 50 (-= 100)  --> Transfer(victim, attacker, 50)
```

!!! note

    This is the basic case. If the attacker has a bot with more logic they could abort/adapt their transfer in the reverse scenario.

### Detection

From the traces that happened on the blockchain, we can check if:

- both transactions write to the same key and storage address
- there is a `Transfer(victim, attacker, n)` and later a `Approval(victim, attacker, m)`
- the victim writes the value `m`