# Kybra-Unique-Principal-ID
ICP network - Passport attestation of princpipal ID - backend (Kybra)

## Commands
 * Start the server
   
```sh
dfx start (--background) (--clean) # clean is to delete all (private) chain
```

* Deploy

```sh
dfx deploy port (--newtork ic) --verbose --argument '(principal "admin-prinpical-id")' # use --network -ic to deploy on public chain 
```

 * Get info if prinpipal is attested:
   
```sh
dfx canister call <<<<>>>>>> is_attested '(principal "<<<<>>>>>>>>"))
```

 * Get attestation:
   
```sh
dfx canister call <<<<>>>>>> get_attestation '(principal "<<<<>>>>>>>>")
```

 * Other usefull commands

```sh
dfx identity new user  # creating new user (use --disable-encryption in Kybra!)
dfx identity list # list of ussers
dfx identity use user1 # change active user
dfx identity get-principal # get principal
```

## Warning
 * Kybra only work with unencrypted identities!
