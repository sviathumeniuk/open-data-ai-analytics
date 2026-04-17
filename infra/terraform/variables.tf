variable "compartment_id" {
  description = "OCID вашого компартменту в OCI"
  type        = string
}

variable "region" {
  description = "Регіон OCI (наприклад, eu-stockholm-1)"
  type        = string
}

variable "ssh_public_key" {
  description = "Публічний SSH-ключ для доступу до інстансу"
  type        = string
}
