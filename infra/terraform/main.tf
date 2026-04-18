provider "oci" {
  region = "eu-stockholm-1"
}

variable "compartment_id" {
  default = "ocid1.tenancy.oc1..aaaaaaaalmch37h7xdztb6gwgtyxipex7zpyzz6ya2gmdznpsy7owqreapha"
}

variable "ssh_public_key" {
  default = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQCx+GgXDYmkapBdUVn2INbPbxeo8+sKy9bGT36E5R8af4M2kF12PoOGJF76pZ9j9B03CWCNb96kCFxT+gbYvtcR+a/Z0bNlCT7smFjyrm6jb8/8fntJTx+hF3KCchxX/5YZGgR0EvOFVXEZyHEl+j4KpHv/OIxWsqi8Aa8FFWoIhXpoRKyNxPUtG65I8QptmzLOlnY1V11qb2KqG/64bbWuGdDtewPoP7hbvXAh/XjxxxjKYGH8ibpgirJLjlztogHOy47UkIrvXpcZkubk6FDfTOuy1jxkYkS8VT7mm05j4pEuIL8hD2QnvwNCVAUTXVzapMrvXYl9wbCGpdrZCsTBLQPGaI2DJhEDk+vob9w1zGY6Fun02mqePsOzn5BYb5r3zpZBbfcUTOMOuUcJsWhynuj8VX9GmnSqlXS2B3EAf6dtiixlzI3bATx4hGxv3n/hF/SA1HgcRjvCQ6w7VcaEdfNOwLTRDpZhTN5UKaLrhV++3nnzFPAv6TqpZ2SJI5d+cQQcIvnzEwl/6VetOhR0H/i7+5vGfUgFynLZhaRCZNxU28YURyOdNt8tSWtZljB0qzOZJfyiRCFi6nQDq+uXtLMNR9qjYEDbvB+mSOanSFp4o9K7gJHoeXWbPddkYrv4G70IUTndl3af+1w4B6AkGpE5kwYm5wxRbfWtt5MNyw== open-data-ai-analytics"
}

data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

data "oci_core_images" "oracle_linux_9" {
  compartment_id           = var.compartment_id
  operating_system         = "Oracle Linux"
  operating_system_version = "9"
  shape                    = "VM.Standard.E2.1.Micro"
  sort_by                  = "TIMECREATED"
  sort_order               = "DESC"
}

resource "oci_core_vcn" "analytics_vcn" {
  compartment_id = var.compartment_id
  cidr_block     = "10.0.0.0/16"
  display_name   = "analytics_vcn"
  dns_label      = "analytics"
}

resource "oci_core_subnet" "analytics_subnet" {
  compartment_id      = var.compartment_id
  vcn_id              = oci_core_vcn.analytics_vcn.id
  cidr_block          = "10.0.1.0/24"
  display_name        = "analytics_subnet"
  dns_label           = "subnet1"
  security_list_ids   = [oci_core_security_list.analytics_sl.id]
  route_table_id      = oci_core_route_table.analytics_rt.id
}

resource "oci_core_internet_gateway" "analytics_ig" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.analytics_vcn.id
  display_name   = "analytics_ig"
}

resource "oci_core_route_table" "analytics_rt" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.analytics_vcn.id
  display_name   = "analytics_rt"

  route_rules {
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"
    network_entity_id = oci_core_internet_gateway.analytics_ig.id
  }
}

resource "oci_core_security_list" "analytics_sl" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.analytics_vcn.id
  display_name   = "analytics_security_list"

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6"
    source   = "0.0.0.0/0"
    tcp_options {
      min = 8000
      max = 8000
    }
  }

  egress_security_rules {
    protocol    = "all"
    destination = "0.0.0.0/0"
  }
}

resource "oci_core_instance" "analytics_instance" {
  compartment_id      = var.compartment_id
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "analytics-amd-vm"
  shape               = "VM.Standard.E2.1.Micro"

  create_vnic_details {
    subnet_id        = oci_core_subnet.analytics_subnet.id
    display_name     = "primary-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    source_id   = data.oci_core_images.oracle_linux_9.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(file("cloud-init.yaml"))
  }

  preserve_boot_volume = false
}

output "instance_public_ip" {
  value = oci_core_instance.analytics_instance.public_ip
}
