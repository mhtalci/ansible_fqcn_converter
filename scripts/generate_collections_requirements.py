#!/usr/bin/env python3
"""
Generate Ansible Collections Requirements File

This script generates a comprehensive requirements.yml file for all Ansible collections
supported by the FQCN converter, using Context7 documentation for accurate version information.

Usage:
    python3 scripts/generate_collections_requirements.py [--output requirements.yml] [--include-all]
"""

import argparse
import yaml
import sys
from pathlib import Path


def load_fqcn_mapping():
    """Load the FQCN mapping configuration."""
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


def generate_requirements(config, include_all=False):
    """Generate collections requirements from FQCN mapping."""
    requirements = {"collections": []}

    # Get collection dependencies
    dependencies = config.get("collection_dependencies", {})

    # Core collections that should always be included
    core_collections = [
        "ansible.posix",
        "community.general",
        "community.docker",
        "community.vmware",
        "community.dns",
        "community.crypto",
    ]

    # Add core collections
    for collection_name in core_collections:
        if collection_name in dependencies:
            deps = dependencies[collection_name]
            if deps:  # If there are version requirements
                for dep in deps:
                    requirements["collections"].append(
                        {"name": dep["name"], "version": dep["version"]}
                    )
            else:
                requirements["collections"].append({"name": collection_name})
        else:
            requirements["collections"].append({"name": collection_name})

    # Add additional collections if include_all is True
    if include_all:
        additional_collections = [
            "community.proxmox",
            "community.routeros",
            "community.mysql",
            "community.postgresql",
            "community.mongodb",
            "community.zabbix",
            "community.windows",
            "community.network",
            "community.libvirt",
            "community.kubernetes",
            "community.grafana",
            "community.rabbitmq",
            "community.sap_libs",
            "community.sops",
            "community.hashi_vault",
            "community.okd",
            "community.digitalocean",
            "community.aws",
            "community.azure",
            "community.google",
            "ansible.windows",
            "ansible.netcommon",
            "ansible.utils",
            "kubernetes.core",
            "cisco.ios",
            "cisco.iosxr",
            "cisco.nxos",
            "cisco.asa",
            "arista.eos",
            "juniper.device",
            "vyos.vyos",
            "amazon.aws",
            "azure.azcollection",
            "google.cloud",
            "dellemc.openmanage",
            "netapp.ontap",
            "purestorage.flasharray",
            "f5networks.f5_modules",
            "fortinet.fortios",
            "paloaltonetworks.panos",
            "checkpoint.mgmt",
            "ovirt.ovirt",
            "redhat.openshift",
            "redhat.rhv",
            "servicenow.servicenow",
            "splunk.es",
            "ibm.qradar",
            "datadog.dd",
            "newrelic.observability",
            "cyberark.pas",
            "hashicorp.vault",
            "chocolatey.chocolatey",
            "netbox.netbox",
            "theforeman.foreman",
            "awx.awx",
        ]

        for collection_name in additional_collections:
            # Avoid duplicates
            if not any(
                c.get("name") == collection_name for c in requirements["collections"]
            ):
                if collection_name in dependencies:
                    deps = dependencies[collection_name]
                    if deps:
                        for dep in deps:
                            requirements["collections"].append(
                                {"name": dep["name"], "version": dep["version"]}
                            )
                    else:
                        requirements["collections"].append({"name": collection_name})
                else:
                    requirements["collections"].append({"name": collection_name})

    # Sort collections by name for consistency
    requirements["collections"].sort(key=lambda x: x["name"])

    return requirements


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Generate Ansible Collections Requirements File",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Generate core collections requirements
    python3 scripts/generate_collections_requirements.py
    
    # Generate comprehensive requirements with all collections
    python3 scripts/generate_collections_requirements.py --include-all
    
    # Save to custom file
    python3 scripts/generate_collections_requirements.py --output my-requirements.yml
        """,
    )

    parser.add_argument(
        "--output",
        "-o",
        default="requirements.yml",
        help="Output file path (default: requirements.yml)",
    )

    parser.add_argument(
        "--include-all",
        action="store_true",
        help="Include all available collections, not just core ones",
    )

    args = parser.parse_args()

    # Load FQCN mapping configuration
    config = load_fqcn_mapping()

    # Generate requirements
    requirements = generate_requirements(config, args.include_all)

    # Write requirements file
    try:
        with open(args.output, "w") as f:
            f.write("---\n")
            f.write("# Ansible Collections Requirements\n")
            f.write("# Generated by FQCN Converter\n")
            f.write(
                "# Install with: ansible-galaxy collection install -r requirements.yml\n\n"
            )
            yaml.dump(requirements, f, default_flow_style=False, sort_keys=False)

        print(f"✅ Requirements file generated: {args.output}")
        print(f"📦 Collections included: {len(requirements['collections'])}")

        if args.include_all:
            print("🌟 Comprehensive collection set included")
        else:
            print("🎯 Core collections included (use --include-all for more)")

        print(f"\n📋 To install collections:")
        print(f"   ansible-galaxy collection install -r {args.output}")

    except Exception as e:
        print(f"Error writing requirements file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
