#!/usr/bin/env bash
# Runs when a lab is pre-warmed from Vocareum's fleet dashboard, ahead of any
# student arriving.
#
# This hook is where work slow enough that a student should not wait for it
# belongs. It runs per lab rather than per student, and it is handed
# VOC_DB_USER_EMAIL and VOC_IPC_DATA_FILE anyway, so a script written here can
# look per-student without being per-student. This version records which it turns
# out to be and provisions nothing.
#
# It provisions no compute, and that is a deliberate reversal. An earlier version
# warmed the student's cluster from here whenever VOC_DB_USER_EMAIL arrived, on
# the reasoning that resolving a connector from Maven and installing ten pypi
# packages is several minutes a student should not sit
# through. Measured on 2026-08-05, that reasoning does not survive how Vocareum
# names a lab identity. Vocareum mints a Databricks principal per session and
# deletes it afterward, and the local part of the address carries the session's
# start epoch: labuser16089549_1785948805 for one session and
# labuser16089549_1785972938 for the next, same student. cluster_name_for in
# voclab.py keys idempotency on that local part, so a cluster warmed here and the
# cluster user_setup.sh guarantees carry different names whenever the two runs
# belong to different sessions, which is every case a pre-warm is for. Warming
# produced a second cluster rather than a head start.
#
# The second cluster is worse than wasted, because cluster_release keys on the
# same name. lab_end.sh runs against the student's own session and names the
# student's own cluster, so a cluster warmed under any other name is invisible to
# cleanup and nothing but DEFAULT_AUTOTERMINATION_MINUTES ever reclaims it.
# Warming compute from here bought no time and left a cluster billing for an hour
# and a half, which is the reverse of the trade it was made for.
#
# What still belongs here is pre-warm work not named after a student: an instance
# pool, a dataset staged into a volume, a catalog. The cost the deleted path was
# aimed at is real and still unpaid. Measured the same day, a cluster takes about
# 10 minutes to reach RUNNING and its eleven libraries another 6 to reach
# INSTALLED, so a student waits about 16 minutes for a usable cluster and the
# cluster reports RUNNING for the last 6 of them.
#
# Environment Vocareum documents for this hook:
#   VOC_DB_WORKSPACE_URL   the workspace being warmed
#   VOC_PARTID             the assignment part
#   VOC_LABID              the lab identifier
#   VOC_DB_USER_EMAIL      a lab identity, if one is associated this early, and
#                          measured to be a different identity from the one the
#                          student's own session carries
#   VOC_CUSTOM_DATA        voccustomdata.txt from workspace_init.sh, when it ran
#   VOC_IPC_DATA_FILE      write notebook_url here to choose the landing page
#   VOC_RESOURCE_TAGS      tags to put on anything billable this script creates,
#                          unused while it creates nothing

set -euo pipefail

VOC_SCRIPT_NAME="lab_setup.sh"

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
        "Vocareum did not set VOC_DB_WORKSPACE_URL, so this script cannot tell which workspace it is warming."
fi

workspace_id="$(voc_workspace_id "$workspace_url")"
voc_log "workspace_url=$workspace_url"
voc_log "workspace_id=${workspace_id:-not-in-url}"
voc_log "part=${VOC_PARTID:-unset} lab=${VOC_LABID:-unset}"

# Whether Vocareum associated a user this early is recorded and acted on no
# further. It is worth recording because it is the thing that decides whether a
# per-student pre-warm could ever work, and the header explains why the answer is
# no even when a user does arrive: the identity is a different one from the
# student's own session, so its name is a different name. Recording it keeps the
# finding checkable against a later Vocareum change rather than settled by this
# comment.
if [ -n "${VOC_DB_USER_EMAIL:-}" ]; then
    voc_log "a user is associated this early: ${VOC_DB_USER_EMAIL}"
    voc_log "not warming a cluster for it, because the name it would carry is"
    voc_log "not the name the student's own session will look for"
    user_scope="per-user"
else
    voc_log "no user is associated yet, so this hook ran ahead of any student"
    user_scope="per-lab"
fi

voc_log "no compute is provisioned here; user_setup.sh creates the cluster"

# No notebook URL is written here. user_setup.sh runs after this hook and writes
# its own, and two scripts writing the same file is a race whose winner is not
# documented. Leaving the landing page to the later script keeps that decision in
# one place.
voc_log "leaving the landing page to user_setup.sh"

# cluster_name and cluster_action are gone from this record along with the path
# that filled them. A field reading none on every run is a field a reader has to
# rule out before believing the cluster came from user_setup.sh, and the record
# from user_setup.sh already names it.
voc_custom_write "$(
    printf '%s, %s, %s, %s' \
        "$(voc_custom_field ran_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')")" \
        "$(voc_custom_field script "$VOC_SCRIPT_NAME")" \
        "$(voc_custom_field workspace_id "${workspace_id:-unknown}")" \
        "$(voc_custom_field user_scope "$user_scope")"
)"

voc_log "done"
exit 0
