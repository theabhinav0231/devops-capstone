# Least-privilege CI/CD secret policy for CloudLedger
path "secret/data/capstone-abhinav/cloudledger" {
  capabilities = ["read"]
}
path "secret/metadata/capstone-abhinav/cloudledger" {
  capabilities = ["read"]
}
