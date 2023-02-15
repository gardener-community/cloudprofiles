openstack flavor list -f yaml | yq 'map(.name = .Name
                              | del(.Name)
                              | .memory = .RAM
                              | del(.RAM)
                              | .cpu = .VCPUs
                              | del(.VCPUs)
                              | del(.["Is Public"])
                              | del(.Ephemeral)
                              | del(.ID)
                              | del(.Disk))'
