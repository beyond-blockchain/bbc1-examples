RFID Logistics
==========
This app provides simple Web APIs and a command line tool to demonstrate how we can provide 'proof of authenticity of logistics information with passive RFID tags and blockchain'. Based on our paper available at arXiv : https://arxiv.org/abs/2011.05442

RFID service (General App) : the following set of API is provided:
* **/rfid-api/certificate** [GET] returns a certificate for a public key stated valid for the specified point of time.
* **/rfid-api/readout** [POST] registers a single readout (used by a reader).
* **/rfid-api/readouts** [GET] returns a set of readouts matching the input.
* **/rfid-api/setup** [POST] sets the environment (a simple database).

Evidence service (BBc-1 App) : the following set of API is provided:
* **/evi-api/evidence** [POST] registers a single evidence, used by a reader (for readouts) or a vendor (for public key certificates).
* **/evi-api/proof** [GET] returns the proof spec and Merkle subtree for an evidence.
* **/evi-api/verify** [GET] verifies an evidence accompanied with the proof structure (provided for convenience).
* **/evi-api/setup** [POST] sets the environment (a BBc-1 domain and a simple database).


## Dependencies
* bbc1 >= 1.5
* py-bbclib >= 1.6
* bbc1-lib-std >= 0.19
* bbc1-lib-registry >= 0.8
* ledger_subsystem >= 0.15
* Flask >= 1.1.2

Although we will redesign bbc1-libs and ledger_subsystem shortly.

## Installing dependencies
You need to pip-install bbc1 and Flask. Others (BBc-1 libraries bbc1-lib-?? and ledger_subsystem) are currently at their late development stages, and you will need to do `git clone -b develop [URI]`  to clone the project's development branch, go to the project directory and `python setup.py sdist` to generate an installer tar ball, and then `pip install dist/[tar.gz file]`.

* For further information on installing and using bbc1, see [tutorials](https://github.com/beyond-blockchain/bbc1/tree/develop/docs)
* Those tutorials are in Japanese for the time being.

## RFID readout, its evidence and public key certificates
**Sample RFID readout**
```
{
  "key": 1,
  "tag": "E28338002000010000750233",
  "timestamp": 1630727723,
  "location": {
    "latitude": "3569.1741N",
    "longitude": "13977.0859E",
    "altitude": "5"
  },
  "data": "",
  "algo": 2,
  "sig": "1bff4a4d5c81603875e0b795731ce2fb86c6a770768919811b6959fb1fd7ab92c9eb5eb06e4163b1c1035d7b1ae913828b7b670c0555b8e90ba5c49fd198ed13",
  "pubkey": "04c7c6885a3bb9349c2fb77be8abbbdc375177751c2e2addadddf3798e35afe0449b9636155ac5f0021de4d4e6583d281789ff8789cd933ba6641d9765a84e7a68"
}
```
**Sample evidence** (of the above readout)
```
{
  "digest_1": "651e24bae1268e2d0913ad503ae052bf21b5e62792e670fdc86a617d07f4a1a3",
  "digest_2": "d98a3742a3e33d0c14b29fe5d3b1dfaa43d5a77a7e4f889503f33ea6e99f2575",
  "algo": "ecdsa-p256v1",
  "sig": "1bff4a4d5c81603875e0b795731ce2fb86c6a770768919811b6959fb1fd7ab92c9eb5eb06e4163b1c1035d7b1ae913828b7b670c0555b8e90ba5c49fd198ed13",
  "pubkey": "04c7c6885a3bb9349c2fb77be8abbbdc375177751c2e2addadddf3798e35afe0449b9636155ac5f0021de4d4e6583d281789ff8789cd933ba6641d9765a84e7a68"
}
```
Specifically, the tag ID, as well as other information, is kept private from the evidence service, while the service is capable (not currently implemented as API) of making a search over "digest_1" values (which is the digest of "key" and "tag" values concatinated).

**Sample public key certificate**
```
{
  "public_key": "04c7c6885a3bb9349c2fb77be8abbbdc375177751c2e2addadddf3798e35afe0449b9636155ac5f0021de4d4e6583d281789ff8789cd933ba6641d9765a84e7a68",
  "issued_at": 1630727615,
  "expires_at": 1662263615,
  "algo": "ecdsa-p256v1",
  "sig": "bfb30eee8b30546229a633fa4800ac310c2cf6eff1a51a4a8fec1baaded9afe8ccbfba083fb5785986920bbeadf15d55aeac5cb24150687ba808d5c36f2a7040",
  "pubkey": "0440048c9aac3040189a0f2c6eb4ef164a8b012f40e0a4fde9e0065a39a4410c3820f9a99078ce66f355157fd755612945f14a06b1a0f65fef3cbd852b8137442f"
}
```

Before verification, these dictionary structures are accompanied with a 'proof' structure that has the specification for how blockchain was used and a Merkle subtree, the same as our 'certify-web' example.

## How to use this example
Below, it is assumed that "bbc_core.py" runs at the user's home directory, and Ethereum's ropsten testnet is used (and you have a sufficient amount of ETH (1 would be more than enough) in an account in ropsten). At first, "bbc_core.py" should be stopped.

1. Set up ledger subsystem (this writes to BBc-1 core's config file)
    ```
    eth_subsystem_tool.py -w ~/.bbc1 auto [infura.io project ID] [private key]
    ```
    Take note (make copy) of the displayed contract address that was deployed by the command above.

2. Start bbc_core.py

3. Set up the API

    POST 'api/setup' to set up.
    ```shell
    $ curl -X POST http://IP_ADDRESS:PORT/evi-api/setup
    {"domain_id": DOMAIN_ID} # returned
    $ curl -X POST http://IP_ADDRESS:PORT/rfid-api/setup
    {} # returned
    ```

4. Stop bbc_core.py (because again we will write to BBc-1 core's config file)

5. Configure Merkle tree settings of the ledger subsystem

    ```
    eth_subsystem_tool.py -w ~/.bbc1 -d [domain id] config_tree [number of documents] [seconds]
    ```
        
    This configures the subsystem so that Merkle tree is closed and Merkle root is written to a Ethereum blockchain (ropsten by default) upon reaching either the specified number of processed documents or the specified seconds.

6. Start bbc_core.py

7. Start index.py of this example

    By default, the server runs at "http://localhost:5000/logi".

**reader_tool.py** is a utility program to set up the RFID vendor and readers, each of which has a unique key-pair, and to run readers either through serial interfaces or by simulation. First, do the following:

```
python reader_tool.py setup
```

This creates a vendor keypair and a configuration file 'config.json'. Other than `setup` the following commands are available:
* **list** : lists the names of existing readers.
* **list_pubkey** : lists the public keys of existing readers.
* **new** {simulated, cdexcru920mj} NAME DEVICE LATITUDE LONGITUDE ALTITUDE : registers a new reader.
  * **NAME** : name of the reader.
  * **DEVICE** : path of the device file or simulated input text file (see 'sim-data.txt' as an example)
  * **LATITUDE, LONGITUDE, ALTITUDE** : GPS location of the reader.
* **remove** NAME : removes the specified reader.
* **run** NAME : runs the specified reader; logger messages are put to a file named 'NAME.log'; execution can be stopped by a keyboard interrupt (ctrl+C).
* **verify** {NAME, vendor}: verifies the certificate for a reader (signed by the vendor) or the vendor (self-signed).
