variable "compartment_id" {
  description = "OCI compartment OCID"
  type        = string
}

variable "region" {
  description = "OCI region (e.g., eu-stockholm-1)"
  type        = string
}

variable "ssh_public_key" {
  description = "Public SSH key for instance access"
  type        = string
}
