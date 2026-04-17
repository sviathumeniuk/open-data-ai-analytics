provider "oci" {
  region = var.region
}

# Динамічний пошук доступних доменів (Availability Domains)
data "oci_identity_availability_domains" "ads" {
  compartment_id = var.compartment_id
}

# Динамічний пошук останнього образу Oracle Linux 9 для ARM (A1.Flex)
data "oci_core_images" "oracle_linux_9" {
  compartment_id = var.compartment_id
  operating_system = "Oracle Linux"
  operating_system_version = "9"
  shape = "VM.Standard.A1.Flex"
  sort_by = "TIMECREATED"
  sort_order = "DESC"
}

# 1. Мережева інфраструктура (VCN та Subnet)
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

# 2. Список безпеки (відкриття портів 22 та 8000)
resource "oci_core_security_list" "analytics_sl" {
  compartment_id = var.compartment_id
  vcn_id         = oci_core_vcn.analytics_vcn.id
  display_name   = "analytics_security_list"

  ingress_security_rules {
    protocol = "6" # TCP
    source   = "0.0.0.0/0"
    tcp_options {
      min = 22
      max = 22
    }
  }

  ingress_security_rules {
    protocol = "6" # TCP
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

# 3. Compute інстанс (VM ARM Always Free)
resource "oci_core_instance" "analytics_instance" {
  compartment_id      = var.compartment_id
  # Використання першого знайденого AD
  availability_domain = data.oci_identity_availability_domains.ads.availability_domains[0].name
  display_name        = "analytics-arm-vm"
  shape               = "VM.Standard.A1.Flex"

  shape_config {
    ocpus         = 1
    memory_in_gbs = 4
  }

  create_vnic_details {
    subnet_id        = oci_core_subnet.analytics_subnet.id
    display_name     = "primary-vnic"
    assign_public_ip = true
  }

  source_details {
    source_type = "image"
    # Використання найсвіжішого знайденого образу
    source_id   = data.oci_core_images.oracle_linux_9.images[0].id
  }

  metadata = {
    ssh_authorized_keys = var.ssh_public_key
    user_data           = base64encode(file("cloud-init.yaml"))
  }

  preserve_boot_volume = false
}

# 4. Вихідні дані (Outputs)
output "instance_public_ip" {
  value       = oci_core_instance.analytics_instance.public_ip
  description = "Публічна IP-адреса вашої аналітичної платформи"
}
