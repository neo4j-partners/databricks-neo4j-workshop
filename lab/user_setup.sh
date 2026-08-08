#!/usr/bin/env bash
# Runs when a student starts the lab. The only required hook.
#
# It does four things, in this order: measures its own environment and reports
# it through the one channel that survives, makes sure the student has a cluster,
# imports the course's notebooks into their workspace folder, and hands them the
# first of those as a landing page. The order is the point. The measurement is first
# because it is what a later reader needs whether or not the rest worked, and the
# landing page is last because sending a student to a notebook with no compute
# attached produces a bug report about the notebook.
#
# The cluster itself is provisioned by voclab.py, which this script reaches
# through voc_voclab. Per student, single node, single user, named after the
# student's lab identity. lab_setup.sh runs the same call to pre-warm it when
# Vocareum gives it a student to warm one for, and the call is idempotent on the
# cluster name, so this script is the guarantee rather than a duplicate.
#
# Environment Vocareum documents for this hook:
#   VOC_DB_WORKSPACE_URL   the workspace the student was placed in
#   VOC_DB_USER_EMAIL      the lab identity Vocareum created for the student
#   VOC_DB_GROUP_NAME      the group that carries the student's permissions
#   VOC_CUSTOM_DATA        voccustomdata.txt from lab_setup.sh, when it ran
#   VOC_IPC_DATA_FILE      write notebook_url here to choose the landing page
#   VOC_RESOURCE_TAGS      tags to put on anything billable this script creates

set -euo pipefail

VOC_SCRIPT_NAME="user_setup.sh"

# voclib.sh is searched for rather than sourced from one path, and the failure
# branch is spelled out here rather than delegated, because voc_fail lives in the
# file being loaded. The header of voclib.sh records the session that made this
# necessary.
voc_lib=""
for candidate in "$(dirname "$0")/voclib.sh" /voc/scripts/voclib.sh \
    ./voclib.sh; do
    if [ -f "$candidate" ]; then
        voc_lib="$candidate"
        break
    fi
done
if [ -z "$voc_lib" ]; then
    voc_stamp="$(date -u '+%Y-%m-%dT%H:%M:%SZ')"
    voc_message="voclib.sh was not beside the hook, in /voc/scripts, or in"
    voc_message="$voc_message the working directory, so this hook could not"
    voc_message="$voc_message load its shared functions."
    printf '{"ran_at": "%s", "script": "%s", "error_code": "%s", ' \
        "$voc_stamp" "$VOC_SCRIPT_NAME" MISSING_VOCLIB > voccustomdata.txt
    printf '"message": "%s"}\n' "$voc_message" >> voccustomdata.txt
    printf '%s: no voclib.sh, wrote MISSING_VOCLIB\n' "$VOC_SCRIPT_NAME" >&2
    exit 1
fi
# shellcheck source=voclib.sh
. "$voc_lib"

voc_log "starting"
voc_report_env

# Before the first guard, so that the one failure mode this lab most suspects is
# not also the one that writes nothing readable. voc_fail overwrites this with
# the failure code, and the landing page below overwrites it on the success
# path, so the record ends up saying which of the three happened. See
# voc_ipc_beacon in voclib.sh for why notebook_url is the field it has to use.
voc_ipc_beacon entered

# The workspace URL is the one value this script cannot proceed without: it
# names the environment the student was placed in, and a landing page cannot be
# formed without it. Failing here is better than handing back a malformed URL,
# because a student sent to a broken page reports a broken lab with no cause.
workspace_url="${VOC_DB_WORKSPACE_URL:-}"
if [ -z "$workspace_url" ]; then
    voc_fail MISSING_WORKSPACE_URL \
        "Vocareum did not set VOC_DB_WORKSPACE_URL, so this script cannot tell which workspace the student is in."
fi

user_email="${VOC_DB_USER_EMAIL:-}"
group_name="${VOC_DB_GROUP_NAME:-}"
workspace_id="$(voc_workspace_id "$workspace_url")"
credential="$(voc_detect_credential)"

voc_log "workspace_url=$workspace_url"
voc_log "workspace_id=${workspace_id:-not-in-url}"
voc_log "user_email=${user_email:-unset}"
voc_log "group_name=${group_name:-unset}"
voc_log "reachable credentials and tools: ${credential:-none}"

# The second value this script cannot proceed without, now that it provisions
# rather than only reports. A per-student cluster is named after the student, so
# without an identity there is nothing to name and nothing to grant to.
if [ -z "$user_email" ]; then
    voc_fail MISSING_USER_EMAIL \
        "Vocareum did not set VOC_DB_USER_EMAIL, so this script cannot tell which student's cluster to provision."
fi

# The cluster, before the landing page. A student sent to a notebook with no
# compute attached reads that as a broken lab, and the failure they report is the
# notebook rather than the provisioning, so it is better to fail here and say so.
#
# The same call lab_setup.sh makes. When the lab was pre-warmed this finds the
# cluster already there and starts it if it has since terminated; when it was
# not, this is what creates it. Idempotent on the cluster name, so which of the
# two happened does not change what the student ends up with, only how long they
# wait for it.
voc_log "provisioning the cluster for $user_email"
if ! voc_voclab cluster-ensure --user "$user_email"; then
    voc_fail "${voclab_error_code:-CLUSTER_ENSURE_FAILED}" \
        "${voclab_message:-voclab.py cluster-ensure failed without naming a reason.}"
fi
# Copied out rather than read later. voc_voclab clears every voclab_ variable
# before each call, so the notebook-import below would leave nothing of this one
# for voc_custom_write at the bottom to record.
cluster_name="${voclab_cluster_name}"
cluster_action="${voclab_cluster_action}"
voc_log "cluster $cluster_name: $cluster_action, ${voclab_cluster_state}"
voc_log "libraries requested this run: ${voclab_libraries_requested}"

# The course's notebooks, which no other part of Vocareum will deliver. They were
# expected to arrive through /voc/startercode; measured in Student View on
# 2026-08-05, startercode reaches the Vocareum environment beside Databricks and
# the student's Databricks folder was empty. So the notebooks travel in
# /voc/scripts with these hooks and this call copies them in.
#
# Idempotent by skipping, not by overwriting. On a stop-then-resume the student
# comes back to the copy they were working in.
voc_log "importing notebooks for $user_email"
if ! voc_voclab notebook-import --user "$user_email"; then
    voc_fail "${voclab_error_code:-NOTEBOOK_IMPORT_FAILED}" \
        "${voclab_message:-voclab.py notebook-import failed without naming a reason.}"
fi
notebook_path="${voclab_notebook_path:-}"
notebook_action="${voclab_notebook_action}"
voc_log "notebooks: $notebook_action, ${voclab_notebook_count} of them"

# The landing page, the first notebook imported rather than the folder holding
# it. A course that ships no notebooks writes no notebook_path, and the beacon
# this hook wrote on entry is left standing instead: overwriting it with a URL
# pointing at nothing would send the student to a blank page and destroy the one
# field that says the hook ran.
#
# Built from the bare origin rather than from VOC_DB_WORKSPACE_URL directly,
# because that variable already carries the ?o= parameter and appending to it
# would produce a URL with two query strings.
if [ -n "$notebook_path" ]; then
    origin="$(voc_origin "$workspace_url")"
    landing_url="${origin}/#workspace${notebook_path}"
    if [ -n "$workspace_id" ]; then
        landing_url="${origin}/?o=${workspace_id}#workspace${notebook_path}"
    fi
    voc_ipc_notebook "$landing_url"
else
    voc_log "this course imported no notebooks, so the entry beacon stands"
fi

# Everything worth knowing about this run, in the one place a later reader can
# get at it. lab_end.sh receives this as VOC_CUSTOM_DATA, and the session record
# carries it out to `dbx-vocareum-diagnose`.
voc_custom_write "$(
    printf '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s' \
        "$(voc_custom_field ran_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')")" \
        "$(voc_custom_field script "$VOC_SCRIPT_NAME")" \
        "$(voc_custom_field workspace_id "${workspace_id:-unknown}")" \
        "$(voc_custom_field user_email "${user_email:-unset}")" \
        "$(voc_custom_field group_name "${group_name:-unset}")" \
        "$(voc_custom_field credentials_found "${credential:-none}")" \
        "$(voc_custom_field cluster_name "$cluster_name")" \
        "$(voc_custom_field cluster_action "$cluster_action")" \
        "$(voc_custom_field notebook_path "$notebook_path")" \
        "$(voc_custom_field notebook_action "$notebook_action")"
)"

voc_log "done"
exit 0
