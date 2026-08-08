#!/usr/bin/env bash
# Runs once, after Vocareum creates a workspace. Not per student.
#
# This is where anything shared by every student in a workspace belongs: a
# secret scope holding the credentials for an external service, a cluster policy,
# a shared catalog, the SQL warehouse the course runs its statements against.
# Creating those here rather than in user_setup.sh is what keeps 30 students from
# creating 30 copies.
#
# It creates the warehouse and nothing else, which is a floor rather than a
# ceiling. This hook's documented environment does not include VOC_DB_USER_EMAIL
# or VOC_DB_GROUP_NAME, so there is less to work with here than anywhere else,
# and a course adds its own provisioning below rather than finding it here. The
# rest of what this hook does is record that it ran and against which workspace,
# which is how anyone learns whether Vocareum calls it at all and how often.
#
# Environment Vocareum documents for this hook:
#   VOC_DB_WORKSPACE_URL   the workspace that was just created
#   VOC_PARTID             the assignment part this workspace serves
#   VOC_LABID              the lab identifier
#   VOC_RESOURCE_TAGS      tags to put on anything billable this script creates
#
# Note the absences. There is no VOC_IPC_DATA_FILE, because no student is
# waiting on a landing page, and no VOC_DB_GROUP_NAME, because the groups are
# created per student session later.

set -euo pipefail

VOC_SCRIPT_NAME="workspace_init.sh"

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

workspace_url="${VOC_DB_WORKSPACE_URL:-}"
if [ -z "$workspace_url" ]; then
    voc_fail MISSING_WORKSPACE_URL \
        "Vocareum did not set VOC_DB_WORKSPACE_URL, so this script cannot tell which workspace it is initializing."
fi

workspace_id="$(voc_workspace_id "$workspace_url")"
voc_log "workspace_url=$workspace_url"
voc_log "workspace_id=${workspace_id:-not-in-url}"
voc_log "part=${VOC_PARTID:-unset} lab=${VOC_LABID:-unset}"
voc_log "resource tags: ${VOC_RESOURCE_TAGS:-none}"
# Recorded rather than only logged. This hook runs in a different context from
# user_setup.sh, so its answer to the credential question can differ, and a log
# line does not survive: Vocareum does not expose a lifecycle script's standard
# output through its REST API. voccustomdata.txt does survive, into the next
# script as VOC_CUSTOM_DATA and into the session record dbx-vocareum-diagnose
# reads.
credential="$(voc_detect_credential)"
voc_log "reachable credentials and tools: ${credential:-none}"

# A voclab.py token-probe call sat here between 2026-08-08 20:31 and 21:05 UTC,
# to find out whether VOC_DB_API_TOKEN authenticates and whose identity it
# carries. It does, and it is the service principal. The verdicts are in
# dbx-vocareum's docs/permissions.md, which is the only place a permission result
# is allowed to live, and the subcommand is still in voclab.py for anyone who
# needs to ask again. Do not put the call back on the critical path: it is eight
# GETs on every workspace init in exchange for an answer already written down.

# The SQL warehouse, when the course asks for one. One per workspace rather than
# one per student, which is why it is created here: the Statement Execution API
# takes a warehouse_id and nothing else can run SQL from a hook, and a course
# that needs SQL needs it once.
#
# Guarded on the name rather than always run. A warehouse is billable, voclab.py
# refuses to invent a name for one, and a course that runs no SQL is a real
# course, so calling unconditionally would fail this hook over an object nobody
# wanted. Vocareum sets no VOC_DB_GROUP_NAME this early, so the grant is skipped
# and warehouse_granted_to records that; user_setup.sh is where a group exists.
warehouse_name="${VOC_COURSE_WAREHOUSE_NAME:-}"
warehouse_action="skipped"
if [ -n "$warehouse_name" ]; then
    voc_log "ensuring the SQL warehouse $warehouse_name"
    if ! voc_voclab warehouse-ensure; then
        voc_fail "${voclab_error_code:-WAREHOUSE_ENSURE_FAILED}" \
            "${voclab_message:-voclab.py warehouse-ensure failed without naming a reason.}"
    fi
    warehouse_action="${voclab_warehouse_action}"
    voc_log "warehouse $warehouse_name: $warehouse_action, ${voclab_warehouse_state}"
else
    voc_log "this course names no SQL warehouse, so none was created"
fi

# The warehouse this course did not ask for. Databricks creates a starter
# warehouse with every workspace, and Vocareum creates a workspace per part, so a
# size corrected by hand in the console lasts exactly one class. Measured
# 2026-08-08 in workspace 7474646059936391 it was Small, four times the 2X-Small
# shared_warehouse above, carrying a users CAN_USE grant, which is every student.
# A student who opens the SQL editor and takes the default gets the expensive one.
#
# Run unconditionally, unlike the block above, because this object exists whether
# or not the course looked at it. VOC_COURSE_STARTER_WAREHOUSE_SIZE naming no
# size is what declines it, and voclab.py answers that with skipped.
if ! voc_voclab starter-warehouse; then
    voc_fail "${voclab_error_code:-STARTER_WAREHOUSE_FAILED}" \
        "${voclab_message:-voclab.py starter-warehouse failed without naming a reason.}"
fi
voc_log "starter warehouse: ${voclab_starter_warehouse_action}, ${voclab_starter_warehouse_size}"

# This course's own objects: the catalog, the four schemas, the volume, the 27
# courseware files, the DLT pipeline, and the comments and grants Lab 4's Genie
# space reads. All of it shared by every student in this workspace, which is why
# it is here and not in user_setup.sh: 30 students would otherwise run the same
# ETL 30 times against the same tables.
#
# workshop.py rather than more of this hook, because these are REST calls and
# those are not calls worth writing in shell. It is uploaded to /voc/scripts
# beside voclab.py and imports it, so there is one HTTP retry policy and not two.
#
# After the warehouse, and not before: every statement it runs goes through the
# Statement Execution API, which takes a warehouse_id and has nothing to fall
# back on. A course whose course.env names no warehouse cannot reach this.
voc_log "provisioning the workshop's catalog, data, pipeline and Genie comments"
if ! voc_python workshop.py provision; then
    voc_fail "${workshop_error_code:-WORKSHOP_PROVISION_FAILED}" \
        "${workshop_message:-workshop.py provision failed without naming a reason.}"
fi
voc_log "catalog ${workshop_catalog}, ${workshop_data_files_uploaded} files uploaded"
voc_log "pipeline ${workshop_pipeline_id}: ${workshop_pipeline_action}, ${workshop_pipeline_state}"

voc_custom_write "$(
    printf '%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s' \
        "$(voc_custom_field ran_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')")" \
        "$(voc_custom_field script "$VOC_SCRIPT_NAME")" \
        "$(voc_custom_field workspace_id "${workspace_id:-unknown}")" \
        "$(voc_custom_field part_id "${VOC_PARTID:-unset}")" \
        "$(voc_custom_field credentials_found "${credential:-none}")" \
        "$(voc_custom_field warehouse_name "${warehouse_name:-none}")" \
        "$(voc_custom_field warehouse_action "$warehouse_action")" \
        "$(voc_custom_field starter_warehouse_action "${voclab_starter_warehouse_action}")" \
        "$(voc_custom_field catalog "$workshop_catalog")" \
        "$(voc_custom_field data_files_uploaded "$workshop_data_files_uploaded")" \
        "$(voc_custom_field pipeline_state "$workshop_pipeline_state")"
)"

voc_log "done"
exit 0
