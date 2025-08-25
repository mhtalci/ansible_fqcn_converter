#!/usr/bin/env python3
"""
Enhance FQCN Mapping with Official Ansible Collections

This script enhances the FQCN mapping configuration by adding comprehensive
module mappings from official Ansible collections documentation.

Based on: https://docs.ansible.com/ansible/latest/collections/index.html#list-of-collections

Usage:
    python3 scripts/enhance_fqcn_mapping.py [--dry-run] [--output config/fqcn_mapping.yml]
"""

import argparse
import yaml
import sys
from pathlib import Path
from typing import Dict, List, Any


# Comprehensive collection mapping based on official Ansible documentation
OFFICIAL_COLLECTIONS = {
    # Core Ansible Collections
    "ansible.builtin": {
        "description": "Core Ansible modules and plugins",
        "modules": [
            # File operations
            "copy",
            "file",
            "template",
            "lineinfile",
            "replace",
            "blockinfile",
            "find",
            "stat",
            "fetch",
            "synchronize",
            "unarchive",
            "archive",
            "slurp",
            "assemble",
            "tempfile",
            # Package management
            "package",
            "apt",
            "yum",
            "dnf",
            "pip",
            "rpm_key",
            "apt_key",
            "apt_repository",
            "yum_repository",
            # Service management
            "service",
            "systemd",
            # System operations
            "command",
            "shell",
            "script",
            "raw",
            "reboot",
            "wait_for",
            "wait_for_connection",
            # User and group management
            "user",
            "group",
            # Variables and facts
            "set_fact",
            "setup",
            "gather_facts",
            # Control flow
            "include",
            "include_tasks",
            "include_vars",
            "include_role",
            "import_tasks",
            "import_playbook",
            "import_role",
            # Meta operations
            "meta",
            "fail",
            "debug",
            "assert",
            "pause",
            # Network operations
            "uri",
            "get_url",
            # Cron and scheduling
            "cron",
            "at",
            # Mount operations
            "mount",
            # Hostname operations
            "hostname",
            # Git operations
            "git",
            # Additional builtin modules
            "add_host",
            "group_by",
            "known_hosts",
            "validate_argument_spec",
        ],
    },
    "ansible.posix": {
        "description": "POSIX UNIX/Linux and derivative Operating Systems",
        "modules": [
            "acl",
            "at",
            "authorized_key",
            "firewalld",
            "firewalld_info",
            "mount",
            "patch",
            "seboolean",
            "selinux",
            "synchronize",
            "sysctl",
            "profile_roles",
            "profile_tasks",
            "timer",
            "json",
            "jsonl",
            "rhel_facts",
            "rhel_rpm_ostree",
            "rpm_ostree_upgrade",
        ],
    },
    "ansible.windows": {
        "description": "Core plugins supported by Ansible for managing Windows hosts",
        "modules": [
            "win_acl",
            "win_acl_inheritance",
            "win_certificate_store",
            "win_command",
            "win_copy",
            "win_dns_client",
            "win_domain",
            "win_domain_controller",
            "win_domain_membership",
            "win_dsc",
            "win_environment",
            "win_feature",
            "win_file",
            "win_find",
            "win_get_url",
            "win_group",
            "win_group_membership",
            "win_hostname",
            "win_optional_feature",
            "win_owner",
            "win_package",
            "win_path",
            "win_ping",
            "win_powershell",
            "win_reboot",
            "win_reg_stat",
            "win_regedit",
            "win_service",
            "win_service_info",
            "win_share",
            "win_shell",
            "win_stat",
            "win_tempfile",
            "win_template",
            "win_updates",
            "win_uri",
            "win_user",
            "win_user_right",
            "win_wait_for",
            "win_whoami",
        ],
    },
    "ansible.netcommon": {
        "description": "Common networking utilities and plugins",
        "modules": [
            "cli_command",
            "cli_config",
            "net_banner",
            "net_get",
            "net_interface",
            "net_l2_interface",
            "net_l3_interface",
            "net_linkagg",
            "net_lldp",
            "net_lldp_interface",
            "net_logging",
            "net_ping",
            "net_put",
            "net_static_route",
            "net_system",
            "net_user",
            "net_vlan",
            "net_vrf",
            "netconf_config",
            "netconf_get",
            "netconf_rpc",
            "restconf_config",
            "restconf_get",
            "telnet",
        ],
    },
    "ansible.utils": {
        "description": "Utilities for Ansible playbooks and roles",
        "modules": ["cli_parse", "fact_diff", "update_fact", "validate"],
    },
    # Community Collections
    "community.general": {
        "description": "General purpose modules and plugins",
        "modules": [
            # System modules
            "alternatives",
            "capabilities",
            "cronvar",
            "dconf",
            "filesystem",
            "gconftool2",
            "interfaces_file",
            "iptables",
            "iptables_state",
            "java_cert",
            "java_keystore",
            "kernel_blacklist",
            "locale_gen",
            "lvg",
            "lvol",
            "make",
            "modprobe",
            "open_iscsi",
            "osx_defaults",
            "pam_limits",
            "parted",
            "pids",
            "puppet",
            "python_requirements_info",
            "selinux",
            "sefcontext",
            "selogin",
            "seport",
            "snap",
            "sysctl",
            "timezone",
            "ufw",
            "xfconf",
            # Package management
            "apk",
            "composer",
            "cpanm",
            "easy_install",
            "flatpak",
            "flatpak_remote",
            "gem",
            "homebrew",
            "homebrew_cask",
            "homebrew_tap",
            "mas",
            "npm",
            "openbsd_pkg",
            "opkg",
            "pacman",
            "pacman_key",
            "pear",
            "pip_package_info",
            "pipx",
            "pkg5",
            "pkg5_publisher",
            "pkgin",
            "pkgng",
            "pkgutil",
            "portage",
            "portinstall",
            "redhat_subscription",
            "rhsm_release",
            "rhsm_repository",
            "rhn_channel",
            "rhn_register",
            "slackpkg",
            "snap_alias",
            "swdepot",
            "swupd",
            "urpmi",
            "xbps",
            "yarn",
            "zypper",
            "zypper_repository",
            # Notification modules
            "campfire",
            "flowdock",
            "hipchat",
            "irc",
            "jabber",
            "mail",
            "mattermost",
            "mqtt",
            "nexmo",
            "office_365_connector_card",
            "pushbullet",
            "pushover",
            "rocketchat",
            "say",
            "sendgrid",
            "slack",
            "snow_record",
            "snow_record_find",
            "telegram",
            "twilio",
            "typetalk",
            # Web infrastructure
            "apache2_mod_wsgi",
            "apache2_module",
            "htpasswd",
            "jira",
            "letsencrypt",
            "nginx_status_info",
            # Monitoring
            "airbrake_deployment",
            "datadog_event",
            "datadog_monitor",
            "honeybadger_deployment",
            "icinga2_checkcommand",
            "icinga2_feature",
            "icinga2_host",
            "logentries",
            "logentries_msg",
            "logstash_plugin",
            "monit",
            "nagios",
            "newrelic_deployment",
            "pagerduty",
            "pagerduty_alert",
            "pingdom",
            "rollbar_deployment",
            "sensu_check",
            "sensu_client",
            "sensu_handler",
            "sensu_silence",
            "sensu_subscription",
            "stackdriver",
            "statusio_maintenance",
            # Zabbix modules
            "zabbix_action",
            "zabbix_group",
            "zabbix_group_info",
            "zabbix_host",
            "zabbix_host_info",
            "zabbix_hostmacro",
            "zabbix_maintenance",
            "zabbix_map",
            "zabbix_mediatype",
            "zabbix_proxy",
            "zabbix_screen",
            "zabbix_service",
            "zabbix_template",
            "zabbix_template_info",
            "zabbix_user",
            "zabbix_user_info",
            "zabbix_usergroup",
            "zabbix_valuemap",
            # Cloud and infrastructure
            "linode",
            "linode_v4",
            "proxmox",
            "proxmox_kvm",
            "proxmox_template",
            # Version control
            "gitlab_branch",
            "gitlab_deploy_key",
            "gitlab_group",
            "gitlab_hook",
            "gitlab_project",
            "gitlab_project_variable",
            "gitlab_runner",
            "gitlab_user",
            # Keycloak modules
            "keycloak_authentication",
            "keycloak_client",
            "keycloak_clientscope",
            "keycloak_component_info",
            "keycloak_group",
            "keycloak_identity_provider",
            "keycloak_realm",
            "keycloak_role",
            "keycloak_user",
            "keycloak_user_federation",
            # Network modules
            "nmcli",
            # Virtualization
            "lxc_container",
            "lxd_container",
            "lxd_profile",
            # Additional package managers
            "cargo",
            "conan",
        ],
    },
    "community.docker": {
        "description": "Docker modules and plugins",
        "modules": [
            # Container management
            "docker_container",
            "docker_container_copy_into",
            "docker_container_exec",
            "docker_container_info",
            # Image management
            "docker_image",
            "docker_image_build",
            "docker_image_export",
            "docker_image_info",
            "docker_image_load",
            "docker_image_pull",
            "docker_image_push",
            "docker_image_remove",
            "docker_image_tag",
            # Network management
            "docker_network",
            "docker_network_info",
            # Volume management
            "docker_volume",
            "docker_volume_info",
            # Docker Compose
            "docker_compose_v2",
            "docker_compose_v2_exec",
            "docker_compose_v2_pull",
            "docker_compose_v2_run",
            # Docker Swarm
            "docker_swarm",
            "docker_swarm_info",
            "docker_swarm_service",
            "docker_swarm_service_info",
            "docker_node",
            "docker_node_info",
            "docker_stack",
            "docker_stack_info",
            "docker_stack_task_info",
            # Docker secrets and configs
            "docker_secret",
            "docker_config",
            # Docker utilities
            "docker_host_info",
            "docker_login",
            "docker_prune",
            "docker_plugin",
            "docker_context_info",
            "current_container_facts",
        ],
    },
    "community.vmware": {
        "description": "VMware vSphere modules and plugins",
        "modules": [
            # VM management
            "vmware_guest",
            "vmware_guest_info",
            "vmware_guest_powerstate",
            "vmware_guest_tools_upgrade",
            "vmware_guest_tools_info",
            "vmware_guest_network",
            "vmware_guest_disk",
            "vmware_guest_controller",
            "vmware_guest_serial_port",
            "vmware_guest_tpm",
            "vmware_guest_cross_vc_clone",
            "vmware_guest_instant_clone",
            "vmware_guest_file_operation",
            "vmware_guest_storage_policy",
            "vmware_vm_info",
            "vmware_vm_inventory",
            "vmware_vm_shell",
            "vmware_vmotion",
            "vmware_vm_config_option",
            # Host management
            "vmware_host",
            "vmware_host_info",
            "vmware_host_inventory",
            "vmware_host_powerstate",
            "vmware_host_dns",
            "vmware_host_firewall_manager",
            "vmware_host_graphics",
            "vmware_host_lockdown",
            "vmware_host_lockdown_exceptions",
            "vmware_host_snmp",
            "vmware_maintenancemode",
            "vmware_migrate_vmk",
            # Cluster management
            "vmware_cluster_info",
            "vmware_cluster_ha",
            "vmware_cluster_dpm",
            "vmware_cluster_drs_recommendations",
            "vmware_drs_override",
            # Network management
            "vmware_dvswitch",
            "vmware_dvswitch_nioc",
            "vmware_dvswitch_pvlans",
            "vmware_dvs_portgroup",
            "vmware_dvs_portgroup_info",
            "vmware_vswitch",
            "vmware_vm_vss_dvs_migrate",
            # Storage management
            "vmware_target_canonical_info",
            "vmware_vsan_cluster",
            "vmware_vsan_health_info",
            # Content library
            "vmware_content_library_manager",
            "vmware_content_deploy_template",
            "vmware_content_deploy_ovf_template",
            "vmware_deploy_ovf",
            # vCenter management
            "vcenter_folder",
            "vcenter_extension",
            "vcenter_standard_key_provider",
            # Resource management
            "vmware_resource_pool",
            "vmware_object_role_permission",
            # Snapshots
            "vmware_all_snapshots_info",
            # Categories and tags
            "vmware_category",
            # Infrastructure profiles
            "vmware_vc_infraprofile_info",
            # Tools
            "vmware_tools",
        ],
    },
    "community.crypto": {
        "description": "Cryptographic modules and plugins",
        "modules": [
            # Certificate management
            "acme_account",
            "acme_account_info",
            "acme_certificate",
            "acme_certificate_revoke",
            "acme_challenge_cert_helper",
            "acme_inspect",
            # Certificate generation
            "openssl_certificate",
            "openssl_certificate_info",
            "openssl_csr",
            "openssl_csr_info",
            "openssl_dhparam",
            "openssl_pkcs12",
            "openssl_privatekey",
            "openssl_privatekey_info",
            "openssl_publickey",
            "openssl_publickey_info",
            # X.509 certificate management
            "x509_certificate",
            "x509_certificate_info",
            "x509_crl",
            "x509_crl_info",
            # Cryptographic operations
            "openssh_cert",
            "openssh_keypair",
            # LUKS encryption
            "luks_device",
        ],
    },
    "community.dns": {
        "description": "DNS management modules",
        "modules": [
            # DNS record management
            "hosttech_dns_record",
            "hosttech_dns_record_info",
            "hosttech_dns_record_set",
            "hosttech_dns_record_sets",
            # Hetzner DNS
            "hetzner_dns_record",
            "hetzner_dns_record_info",
            "hetzner_dns_record_set",
            "hetzner_dns_record_sets",
            "hetzner_dns_zone",
            "hetzner_dns_zone_info",
            # Generic DNS modules
            "wait_for_txt",
            "nameserver_info",
            "nameserver_record_info",
        ],
    },
    "community.mysql": {
        "description": "MySQL and MariaDB modules",
        "modules": [
            "mysql_db",
            "mysql_info",
            "mysql_query",
            "mysql_replication",
            "mysql_user",
            "mysql_variables",
        ],
    },
    "community.postgresql": {
        "description": "PostgreSQL modules",
        "modules": [
            "postgresql_copy",
            "postgresql_db",
            "postgresql_ext",
            "postgresql_info",
            "postgresql_lang",
            "postgresql_membership",
            "postgresql_owner",
            "postgresql_pg_hba",
            "postgresql_ping",
            "postgresql_privs",
            "postgresql_publication",
            "postgresql_query",
            "postgresql_schema",
            "postgresql_script",
            "postgresql_sequence",
            "postgresql_set",
            "postgresql_slot",
            "postgresql_subscription",
            "postgresql_table",
            "postgresql_tablespace",
            "postgresql_user",
            "postgresql_user_obj_stat_info",
        ],
    },
    "community.mongodb": {
        "description": "MongoDB modules",
        "modules": [
            "mongodb_balancer",
            "mongodb_index",
            "mongodb_info",
            "mongodb_maintenance",
            "mongodb_monitoring",
            "mongodb_oplog",
            "mongodb_parameter",
            "mongodb_replicaset",
            "mongodb_shard",
            "mongodb_shutdown",
            "mongodb_status",
            "mongodb_stepdown",
            "mongodb_user",
        ],
    },
    # Additional collections
    "community.kubernetes": {
        "description": "Kubernetes modules and plugins",
        "modules": [
            "k8s",
            "k8s_info",
            "k8s_scale",
            "k8s_service",
            "k8s_exec",
            "k8s_cp",
            "k8s_drain",
            "k8s_log",
            "helm",
            "helm_info",
            "helm_plugin",
            "helm_plugin_info",
            "helm_repository",
        ],
    },
    "community.aws": {
        "description": "Amazon Web Services modules",
        "modules": [
            "aws_acm",
            "aws_acm_info",
            "aws_api_gateway",
            "aws_application_scaling_policy",
            "aws_batch_compute_environment",
            "aws_batch_job_definition",
            "aws_batch_job_queue",
            "aws_codebuild",
            "aws_codecommit",
            "aws_codepipeline",
            "aws_config_aggregation_authorization",
            "aws_config_aggregator",
            "aws_config_delivery_channel",
            "aws_config_recorder",
            "aws_config_rule",
            "aws_direct_connect_connection",
            "aws_direct_connect_gateway",
            "aws_direct_connect_link_aggregation_group",
            "aws_direct_connect_virtual_interface",
            "aws_eks_cluster",
            "aws_eks_fargate_profile",
            "aws_eks_nodegroup",
            "aws_glue_connection",
            "aws_glue_crawler",
            "aws_glue_job",
            "aws_inspector_target",
            "aws_kms",
            "aws_kms_info",
            "aws_region_info",
            "aws_s3_bucket_info",
            "aws_s3_cors",
            "aws_secret",
            "aws_ses_identity",
            "aws_ses_identity_policy",
            "aws_ses_rule_set",
            "aws_ssm_parameter_store",
            "aws_step_functions_state_machine",
            "aws_waf_condition",
            "aws_waf_info",
            "aws_waf_rule",
            "aws_waf_web_acl",
            "cloudformation_info",
            "cloudformation_stack_set",
            "cloudfront_distribution",
            "cloudfront_info",
            "cloudfront_invalidation",
            "cloudfront_origin_access_identity",
            "cloudtrail",
            "cloudwatchevent_rule",
            "cloudwatchlogs_log_group",
            "cloudwatchlogs_log_group_info",
            "cloudwatchlogs_log_group_metric_filter",
            "data_pipeline",
            "dms_endpoint",
            "dms_replication_subnet_group",
            "dynamodb_table",
            "dynamodb_ttl",
            "ec2_ami_copy",
            "ec2_asg",
            "ec2_asg_info",
            "ec2_customer_gateway",
            "ec2_customer_gateway_info",
            "ec2_eip",
            "ec2_eip_info",
            "ec2_elb",
            "ec2_elb_info",
            "ec2_instance_info",
            "ec2_launch_template",
            "ec2_placement_group",
            "ec2_placement_group_info",
            "ec2_snapshot_copy",
            "ec2_transit_gateway",
            "ec2_transit_gateway_info",
            "ec2_vpc_dhcp_option",
            "ec2_vpc_dhcp_option_info",
            "ec2_vpc_endpoint",
            "ec2_vpc_endpoint_info",
            "ec2_vpc_endpoint_service_info",
            "ec2_vpc_igw",
            "ec2_vpc_igw_info",
            "ec2_vpc_nacl",
            "ec2_vpc_nacl_info",
            "ec2_vpc_nat_gateway",
            "ec2_vpc_nat_gateway_info",
            "ec2_vpc_peer",
            "ec2_vpc_peering_info",
            "ec2_vpc_route_table",
            "ec2_vpc_route_table_info",
            "ec2_vpc_vgw",
            "ec2_vpc_vgw_info",
            "ecs_cluster",
            "ecs_service",
            "ecs_service_info",
            "ecs_task",
            "ecs_taskdefinition",
            "ecs_taskdefinition_info",
            "efs",
            "efs_info",
            "elasticache",
            "elasticache_info",
            "elasticache_parameter_group",
            "elasticache_snapshot",
            "elasticache_subnet_group",
            "elb_application_lb",
            "elb_application_lb_info",
            "elb_classic_lb",
            "elb_classic_lb_info",
            "elb_network_lb",
            "elb_target",
            "elb_target_group",
            "elb_target_group_info",
            "elb_target_info",
            "execute_lambda",
            "iam",
            "iam_cert",
            "iam_group",
            "iam_managed_policy",
            "iam_mfa_device_info",
            "iam_oidc_identity_provider",
            "iam_password_policy",
            "iam_role",
            "iam_role_info",
            "iam_saml_federation",
            "iam_server_certificate_info",
            "iam_user",
            "iam_user_info",
            "lambda",
            "lambda_alias",
            "lambda_event",
            "lambda_info",
            "lambda_policy",
            "lightsail",
            "rds",
            "rds_cluster",
            "rds_instance",
            "rds_instance_info",
            "rds_option_group",
            "rds_option_group_info",
            "rds_param_group",
            "rds_snapshot",
            "rds_snapshot_info",
            "rds_subnet_group",
            "redshift",
            "redshift_cross_region_snapshots",
            "redshift_info",
            "route53",
            "route53_health_check",
            "route53_info",
            "route53_zone",
            "s3_bucket",
            "s3_lifecycle",
            "s3_logging",
            "s3_metrics_configuration",
            "s3_sync",
            "s3_website",
            "sns",
            "sns_topic",
            "sqs_queue",
        ],
    },
    "community.azure": {
        "description": "Microsoft Azure modules",
        "modules": [
            "azure_rm_acs",
            "azure_rm_aduser",
            "azure_rm_aduser_info",
            "azure_rm_aks",
            "azure_rm_aks_info",
            "azure_rm_aksversion_info",
            "azure_rm_applicationsecuritygroup",
            "azure_rm_applicationsecuritygroup_info",
            "azure_rm_appserviceplan",
            "azure_rm_appserviceplan_info",
            "azure_rm_automationaccount",
            "azure_rm_automationaccount_info",
            "azure_rm_autoscale",
            "azure_rm_autoscale_info",
            "azure_rm_availabilityset",
            "azure_rm_availabilityset_info",
            "azure_rm_azurefirewall",
            "azure_rm_azurefirewall_info",
            "azure_rm_batchaccount",
            "azure_rm_cdnendpoint",
            "azure_rm_cdnendpoint_info",
            "azure_rm_cdnprofile",
            "azure_rm_cdnprofile_info",
            "azure_rm_containerinstance",
            "azure_rm_containerinstance_info",
            "azure_rm_containerregistry",
            "azure_rm_containerregistry_info",
            "azure_rm_cosmosdbaccount",
            "azure_rm_cosmosdbaccount_info",
            "azure_rm_deployment",
            "azure_rm_deployment_info",
            "azure_rm_devtestlab",
            "azure_rm_devtestlab_info",
            "azure_rm_devtestlabarmtemplate_info",
            "azure_rm_devtestlabartifact_info",
            "azure_rm_devtestlabartifactsource",
            "azure_rm_devtestlabartifactsource_info",
            "azure_rm_devtestlabcustomimage",
            "azure_rm_devtestlabcustomimage_info",
            "azure_rm_devtestlabenvironment",
            "azure_rm_devtestlabenvironment_info",
            "azure_rm_devtestlabpolicy",
            "azure_rm_devtestlabpolicy_info",
            "azure_rm_devtestlabschedule",
            "azure_rm_devtestlabschedule_info",
            "azure_rm_devtestlabvirtualmachine",
            "azure_rm_devtestlabvirtualmachine_info",
            "azure_rm_devtestlabvirtualnetwork",
            "azure_rm_devtestlabvirtualnetwork_info",
            "azure_rm_dnsrecordset",
            "azure_rm_dnsrecordset_info",
            "azure_rm_dnszone",
            "azure_rm_dnszone_info",
            "azure_rm_functionapp",
            "azure_rm_functionapp_info",
            "azure_rm_gallery",
            "azure_rm_gallery_info",
            "azure_rm_galleryimage",
            "azure_rm_galleryimage_info",
            "azure_rm_galleryimageversion",
            "azure_rm_galleryimageversion_info",
            "azure_rm_hdinsightcluster",
            "azure_rm_hdinsightcluster_info",
            "azure_rm_image",
            "azure_rm_image_info",
            "azure_rm_keyvault",
            "azure_rm_keyvault_info",
            "azure_rm_keyvaultkey",
            "azure_rm_keyvaultkey_info",
            "azure_rm_keyvaultsecret",
            "azure_rm_keyvaultsecret_info",
            "azure_rm_loadbalancer",
            "azure_rm_loadbalancer_info",
            "azure_rm_loganalyticsworkspace",
            "azure_rm_loganalyticsworkspace_info",
            "azure_rm_manageddisk",
            "azure_rm_manageddisk_info",
            "azure_rm_mariadbconfiguration",
            "azure_rm_mariadbconfiguration_info",
            "azure_rm_mariadbdatabase",
            "azure_rm_mariadbdatabase_info",
            "azure_rm_mariadbfirewallrule",
            "azure_rm_mariadbfirewallrule_info",
            "azure_rm_mariadbserver",
            "azure_rm_mariadbserver_info",
            "azure_rm_mysqlconfiguration",
            "azure_rm_mysqlconfiguration_info",
            "azure_rm_mysqldatabase",
            "azure_rm_mysqldatabase_info",
            "azure_rm_mysqlfirewallrule",
            "azure_rm_mysqlfirewallrule_info",
            "azure_rm_mysqlserver",
            "azure_rm_mysqlserver_info",
            "azure_rm_networkinterface",
            "azure_rm_networkinterface_info",
            "azure_rm_networksecuritygroup",
            "azure_rm_networksecuritygroup_info",
            "azure_rm_postgresqlconfiguration",
            "azure_rm_postgresqlconfiguration_info",
            "azure_rm_postgresqldatabase",
            "azure_rm_postgresqldatabase_info",
            "azure_rm_postgresqlfirewallrule",
            "azure_rm_postgresqlfirewallrule_info",
            "azure_rm_postgresqlserver",
            "azure_rm_postgresqlserver_info",
            "azure_rm_publicipaddress",
            "azure_rm_publicipaddress_info",
            "azure_rm_rediscache",
            "azure_rm_rediscache_info",
            "azure_rm_rediscachefirewallrule",
            "azure_rm_resource",
            "azure_rm_resource_info",
            "azure_rm_resourcegroup",
            "azure_rm_resourcegroup_info",
            "azure_rm_roleassignment",
            "azure_rm_roleassignment_info",
            "azure_rm_roledefinition",
            "azure_rm_roledefinition_info",
            "azure_rm_route",
            "azure_rm_routetable",
            "azure_rm_routetable_info",
            "azure_rm_securitygroup",
            "azure_rm_securitygroup_info",
            "azure_rm_servicebus",
            "azure_rm_servicebus_info",
            "azure_rm_servicebusqueue",
            "azure_rm_servicebusqueue_info",
            "azure_rm_servicebussaspolicy",
            "azure_rm_servicebustopic",
            "azure_rm_servicebustopic_info",
            "azure_rm_servicebustopicsubscription",
            "azure_rm_snapshot",
            "azure_rm_snapshot_info",
            "azure_rm_sqldb",
            "azure_rm_sqldb_info",
            "azure_rm_sqldatabase",
            "azure_rm_sqldatabase_info",
            "azure_rm_sqlfirewallrule",
            "azure_rm_sqlfirewallrule_info",
            "azure_rm_sqlserver",
            "azure_rm_sqlserver_info",
            "azure_rm_storageaccount",
            "azure_rm_storageaccount_info",
            "azure_rm_storageblob",
            "azure_rm_subnet",
            "azure_rm_subnet_info",
            "azure_rm_trafficmanagerendpoint",
            "azure_rm_trafficmanagerendpoint_info",
            "azure_rm_trafficmanagerprofile",
            "azure_rm_trafficmanagerprofile_info",
            "azure_rm_virtualmachine",
            "azure_rm_virtualmachine_info",
            "azure_rm_virtualmachineextension",
            "azure_rm_virtualmachineextension_info",
            "azure_rm_virtualmachineimage_info",
            "azure_rm_virtualmachinescaleset",
            "azure_rm_virtualmachinescaleset_info",
            "azure_rm_virtualmachinescalesetextension",
            "azure_rm_virtualmachinescalesetextension_info",
            "azure_rm_virtualmachinescalesetinstance",
            "azure_rm_virtualmachinescalesetinstance_info",
            "azure_rm_virtualnetwork",
            "azure_rm_virtualnetwork_info",
            "azure_rm_virtualnetworkgateway",
            "azure_rm_virtualnetworkgateway_info",
            "azure_rm_virtualnetworkpeering",
            "azure_rm_virtualnetworkpeering_info",
            "azure_rm_webapp",
            "azure_rm_webapp_info",
            "azure_rm_webappslot",
        ],
    },
    "community.google": {
        "description": "Google Cloud Platform modules",
        "modules": [
            "gcp_bigquery_dataset",
            "gcp_bigquery_dataset_info",
            "gcp_bigquery_table",
            "gcp_bigquery_table_info",
            "gcp_cloudbuild_trigger",
            "gcp_cloudbuild_trigger_info",
            "gcp_cloudtasks_queue",
            "gcp_cloudtasks_queue_info",
            "gcp_compute_address",
            "gcp_compute_address_info",
            "gcp_compute_autoscaler",
            "gcp_compute_autoscaler_info",
            "gcp_compute_backend_bucket",
            "gcp_compute_backend_bucket_info",
            "gcp_compute_backend_service",
            "gcp_compute_backend_service_info",
            "gcp_compute_disk",
            "gcp_compute_disk_info",
            "gcp_compute_firewall",
            "gcp_compute_firewall_info",
            "gcp_compute_forwarding_rule",
            "gcp_compute_forwarding_rule_info",
            "gcp_compute_global_address",
            "gcp_compute_global_address_info",
            "gcp_compute_global_forwarding_rule",
            "gcp_compute_global_forwarding_rule_info",
            "gcp_compute_health_check",
            "gcp_compute_health_check_info",
            "gcp_compute_http_health_check",
            "gcp_compute_http_health_check_info",
            "gcp_compute_https_health_check",
            "gcp_compute_https_health_check_info",
            "gcp_compute_image",
            "gcp_compute_image_info",
            "gcp_compute_instance",
            "gcp_compute_instance_group",
            "gcp_compute_instance_group_info",
            "gcp_compute_instance_group_manager",
            "gcp_compute_instance_group_manager_info",
            "gcp_compute_instance_info",
            "gcp_compute_instance_template",
            "gcp_compute_instance_template_info",
            "gcp_compute_network",
            "gcp_compute_network_info",
            "gcp_compute_region_autoscaler",
            "gcp_compute_region_autoscaler_info",
            "gcp_compute_region_backend_service",
            "gcp_compute_region_backend_service_info",
            "gcp_compute_region_disk",
            "gcp_compute_region_disk_info",
            "gcp_compute_region_instance_group_manager",
            "gcp_compute_region_instance_group_manager_info",
            "gcp_compute_route",
            "gcp_compute_route_info",
            "gcp_compute_router",
            "gcp_compute_router_info",
            "gcp_compute_snapshot",
            "gcp_compute_snapshot_info",
            "gcp_compute_ssl_certificate",
            "gcp_compute_ssl_certificate_info",
            "gcp_compute_ssl_policy",
            "gcp_compute_ssl_policy_info",
            "gcp_compute_subnetwork",
            "gcp_compute_subnetwork_info",
            "gcp_compute_target_http_proxy",
            "gcp_compute_target_http_proxy_info",
            "gcp_compute_target_https_proxy",
            "gcp_compute_target_https_proxy_info",
            "gcp_compute_target_pool",
            "gcp_compute_target_pool_info",
            "gcp_compute_target_ssl_proxy",
            "gcp_compute_target_ssl_proxy_info",
            "gcp_compute_target_tcp_proxy",
            "gcp_compute_target_tcp_proxy_info",
            "gcp_compute_target_vpn_gateway",
            "gcp_compute_target_vpn_gateway_info",
            "gcp_compute_url_map",
            "gcp_compute_url_map_info",
            "gcp_compute_vpn_tunnel",
            "gcp_compute_vpn_tunnel_info",
            "gcp_container_cluster",
            "gcp_container_cluster_info",
            "gcp_container_node_pool",
            "gcp_container_node_pool_info",
            "gcp_dns_managed_zone",
            "gcp_dns_managed_zone_info",
            "gcp_dns_resource_record_set",
            "gcp_dns_resource_record_set_info",
            "gcp_iam_role",
            "gcp_iam_role_info",
            "gcp_iam_service_account",
            "gcp_iam_service_account_info",
            "gcp_iam_service_account_key",
            "gcp_logging_metric",
            "gcp_logging_metric_info",
            "gcp_pubsub_subscription",
            "gcp_pubsub_subscription_info",
            "gcp_pubsub_topic",
            "gcp_pubsub_topic_info",
            "gcp_redis_instance",
            "gcp_redis_instance_info",
            "gcp_resourcemanager_project",
            "gcp_resourcemanager_project_info",
            "gcp_sourcerepo_repository",
            "gcp_sourcerepo_repository_info",
            "gcp_spanner_database",
            "gcp_spanner_database_info",
            "gcp_spanner_instance",
            "gcp_spanner_instance_info",
            "gcp_sql_database",
            "gcp_sql_database_info",
            "gcp_sql_instance",
            "gcp_sql_instance_info",
            "gcp_sql_user",
            "gcp_sql_user_info",
            "gcp_storage_bucket",
            "gcp_storage_bucket_access_control",
            "gcp_storage_bucket_info",
            "gcp_storage_object",
            "gcp_storage_object_info",
        ],
    },
}


def load_current_mapping():
    """Load the current FQCN mapping configuration."""
    config_path = Path(__file__).parent.parent / "config" / "fqcn_mapping.yml"

    try:
        with open(config_path, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"Error: FQCN mapping file not found at {config_path}")
        sys.exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing FQCN mapping file: {e}")
        sys.exit(1)


def enhance_mapping(current_config: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance the current mapping with comprehensive collection data."""
    enhanced_config = current_config.copy()

    # Update each collection with comprehensive module mappings
    for collection_key, collection_data in OFFICIAL_COLLECTIONS.items():
        # Convert collection name to config key format
        config_key = collection_key.replace(".", "_")

        # Initialize collection section if it doesn't exist
        if config_key not in enhanced_config:
            enhanced_config[config_key] = {}

        # Add all modules for this collection
        for module_name in collection_data["modules"]:
            enhanced_config[config_key][module_name] = f"{collection_key}.{module_name}"

    # Update collection dependencies
    if "collection_dependencies" not in enhanced_config:
        enhanced_config["collection_dependencies"] = {}

    # Add dependencies for all collections
    for collection_name in OFFICIAL_COLLECTIONS.keys():
        if collection_name not in enhanced_config["collection_dependencies"]:
            if collection_name == "ansible.builtin":
                enhanced_config["collection_dependencies"][collection_name] = []
            else:
                # Determine appropriate version based on collection
                if collection_name.startswith("ansible."):
                    version = ">=1.0.0"
                elif collection_name.startswith("community."):
                    version = ">=2.0.0"
                else:
                    version = ">=1.0.0"

                enhanced_config["collection_dependencies"][collection_name] = [
                    {"name": collection_name, "version": version}
                ]

    # Update requires_collection list
    if "conversion_rules" not in enhanced_config:
        enhanced_config["conversion_rules"] = {}

    if "requires_collection" not in enhanced_config["conversion_rules"]:
        enhanced_config["conversion_rules"]["requires_collection"] = []

    # Add all non-builtin collections to requires_collection
    for collection_name in OFFICIAL_COLLECTIONS.keys():
        if (
            collection_name != "ansible.builtin"
            and collection_name
            not in enhanced_config["conversion_rules"]["requires_collection"]
        ):
            enhanced_config["conversion_rules"]["requires_collection"].append(
                collection_name
            )

    # Sort the requires_collection list
    enhanced_config["conversion_rules"]["requires_collection"].sort()

    return enhanced_config


def save_enhanced_mapping(config: Dict[str, Any], output_path: str):
    """Save the enhanced mapping configuration."""
    try:
        with open(output_path, "w") as f:
            f.write("# FQCN Mapping Configuration\n")
            f.write(
                "# This file defines the mapping from short module names to their Fully Qualified Collection Names (FQCN)\n"
            )
            f.write(
                "# Used by the FQCN conversion script to modernize Ansible playbooks and roles\n"
            )
            f.write(
                "# Enhanced with comprehensive collection support from official Ansible documentation\n"
            )
            f.write(
                "# Source: https://docs.ansible.com/ansible/latest/collections/index.html\n\n"
            )

            yaml.dump(config, f, default_flow_style=False, sort_keys=False, width=120)

        print(f"✅ Enhanced FQCN mapping saved to: {output_path}")

        # Count modules
        total_modules = 0
        for collection_key, collection_data in config.items():
            if isinstance(collection_data, dict) and collection_key not in [
                "collection_dependencies",
                "validation_patterns",
                "conversion_rules",
                "backup_config",
                "rollback_config",
            ]:
                total_modules += len(collection_data)

        print(f"📦 Total modules mapped: {total_modules}")
        print(
            f"🏗️  Collections supported: {len([k for k in config.keys() if k not in ['collection_dependencies', 'validation_patterns', 'conversion_rules', 'backup_config', 'rollback_config']])}"
        )

    except Exception as e:
        print(f"Error saving enhanced mapping: {e}")
        sys.exit(1)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Enhance FQCN Mapping with Official Ansible Collections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Enhance mapping with dry run
    python3 scripts/enhance_fqcn_mapping.py --dry-run
    
    # Enhance and save to default location
    python3 scripts/enhance_fqcn_mapping.py
    
    # Save to custom location
    python3 scripts/enhance_fqcn_mapping.py --output config/enhanced_fqcn_mapping.yml
        """,
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without modifying files",
    )

    parser.add_argument(
        "--output",
        "-o",
        default="config/fqcn_mapping.yml",
        help="Output file path (default: config/fqcn_mapping.yml)",
    )

    args = parser.parse_args()

    print("🔧 Enhancing FQCN mapping with official Ansible collections...")
    print(f"📚 Source: https://docs.ansible.com/ansible/latest/collections/index.html")

    # Load current mapping
    current_config = load_current_mapping()

    # Enhance mapping
    enhanced_config = enhance_mapping(current_config)

    if args.dry_run:
        print("\n🔍 DRY RUN - Changes that would be made:")

        # Show collections that would be added/updated
        for collection_name in OFFICIAL_COLLECTIONS.keys():
            config_key = collection_name.replace(".", "_")
            if config_key in current_config:
                current_modules = set(current_config[config_key].keys())
                new_modules = set(enhanced_config[config_key].keys())
                added_modules = new_modules - current_modules
                if added_modules:
                    print(f"  📦 {collection_name}: +{len(added_modules)} modules")
            else:
                print(
                    f"  🆕 {collection_name}: NEW collection with {len(OFFICIAL_COLLECTIONS[collection_name]['modules'])} modules"
                )

        print(f"\n📊 Summary:")
        current_total = sum(
            len(v)
            for k, v in current_config.items()
            if isinstance(v, dict)
            and k
            not in [
                "collection_dependencies",
                "validation_patterns",
                "conversion_rules",
                "backup_config",
                "rollback_config",
            ]
        )
        enhanced_total = sum(
            len(v)
            for k, v in enhanced_config.items()
            if isinstance(v, dict)
            and k
            not in [
                "collection_dependencies",
                "validation_patterns",
                "conversion_rules",
                "backup_config",
                "rollback_config",
            ]
        )
        print(f"  Current modules: {current_total}")
        print(f"  Enhanced modules: {enhanced_total}")
        print(f"  Added modules: +{enhanced_total - current_total}")

    else:
        # Save enhanced mapping
        save_enhanced_mapping(enhanced_config, args.output)


if __name__ == "__main__":
    main()
