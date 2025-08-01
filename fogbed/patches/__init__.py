"""
Patches para compatibilidade do fogbed
"""

from .cgroups_v2_patch import patch_docker_cgroups, unpatch_docker_cgroups

__all__ = ['patch_docker_cgroups', 'unpatch_docker_cgroups']
