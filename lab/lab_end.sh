#!/usr/bin/env bash
# Runs when a lab ends, whether the student stopped it or it was terminated.
#
# Vocareum stops or terminates the environment on its own, so this hook is not
# what makes the lab end. It is where anything Vocareum does not know about gets
# cleaned up: a cluster this repository's scripts created, a secret scope, a job.
# Anything billable that user_setup.sh brought into existence has to be removed
# here, because Vocareum will not remove what it did not create.
#
# VOC_END_LAB_BEHAVIOR is the variable that decides how much cleanup is correct.
# On "stop" the student's data is preserved for their next session, so deleting
# their notebooks would destroy work they expect to find. On "terminate" the
# environment reverts, so cleanup is free. A script that ignores the distinction
# is either wasteful or destructive, and which one depends on a setting made in
# the Vocareum UI rather than in this file.
#
# What it reclaims is the per-student cluster user_setup.sh provisions, at the
# depth the behavior calls for: terminated on a stop, deleted outright on a
# terminate. Notebooks are left alone in both cases, because nothing here creates
# any. The case statement below records why the stop depth is not the head start
# for the next session it was once written up as.
#
# An earlier version of this hook reclaimed nothing at all unless the value was
# exactly "stop" or exactly "terminate", on the reasoning that an unfamiliar
# instruction is a reason to be conservative. Measured on 2026-08-05, that
# reasoning had the cost backwards. Cluster labuser16089549_1785972938
# (0805-233547-fb7kccnm) was created by user_setup.sh at 23:35:47Z, was still
# RUNNING at 23:51Z with autotermination two hours out, and the session record
# for the part read state Terminated with a sessionend of 22:09:51Z. Whatever
# reclaimed compute in that window, it was not this hook's stop-or-terminate
# case. And GET .../parts/{id} carries no End lab behavior field under any
# spelling, so a value arriving unset or empty is the case to design for rather
# than the exception. Being conservative about the API call is what leaves a
# cluster billing after the student has gone, which nobody notices and nobody
# is paged for.
#
# So the branch below defaults, and it defaults to the shallower of the two
# reclaims. See the case statement for which side that errs on and why.
#
# Environment Vocareum documents for this hook:
#   VOC_DB_WORKSPACE_URL   the workspace the student was in
#   VOC_DB_USER_EMAIL      the lab identity whose session is ending
#   VOC_DB_GROUP_NAME      the group that carried the student's permissions
#   VOC_CUSTOM_DATA        voccustomdata.txt from user_setup.sh
#   VOC_END_LAB_BEHAVIOR   "stop" or "terminate", and measured absent from the
#                          part record, so treat both as unproven at run time
#
# There is no VOC_IPC_DATA_FILE here. No student is being sent anywhere.

set -euo pipefail

VOC_SCRIPT_NAME="lab_end.sh"

# voclib.sh is searched for rather than sourced from one path, and the failure
# branch is spelled out here rather than delegated, because voc_fail lives in the
# file being loaded. The header of voclib.sh records the session that made this
# necessary, and it was this hook that found it.
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

# What arrived, kept verbatim, because it is the thing that made this hook's one
# real failure ambiguous. voccustomdata.txt recorded only the branch that ran,
# so a record reading "nothing was removed" could not be told apart from a hook
# Vocareum never invoked, and the diagnosis cost a day. The raw value goes into
# the record below whatever it is, empty included.
#
# ${VOC_END_LAB_BEHAVIOR+set} tests presence without reading the value, which is
# the distinction set -u makes fatal to ask for any other way. Unset and empty
# are separated because they point at different fixes: unset means this hook is
# not being handed the variable at all, and empty means the part carries no End
# lab behavior setting to hand over.
if [ -n "${VOC_END_LAB_BEHAVIOR+set}" ]; then
    behavior_raw="$VOC_END_LAB_BEHAVIOR"
    behavior_arrived="yes"
else
    behavior_raw=""
    behavior_arrived="no"
fi

# Compared with whitespace removed and case ignored below, so "Terminate\n" is
# matched rather than defaulted. tr rather than ${var,,}, which needs bash 4.2:
# this file's neighbour voclib.sh was bitten by exactly that class of assumption
# with declare -g, on a host carrying bash 3.2.
behavior_word="$(printf '%s' "$behavior_raw" | tr -d '[:space:]')"

user_email="${VOC_DB_USER_EMAIL:-}"
cluster_action="none"
cleanup_error=""

# Which voclab.py subcommand each ending deserves. cluster-stop terminates the
# cluster and keeps its configuration; cluster-remove deletes it outright. Both
# stop the billing, which is the part that matters: Vocareum does not reclaim a
# cluster it did not create.
#
# Not, as this comment used to claim, so that the next session finds the stopped
# cluster by name and skips the Maven resolve. It cannot. The cluster is named
# after the local part of the lab identity, Vocareum mints that identity per
# session, and its local part carries the session's start epoch, so the next
# session looks for a name this one never used. cluster_release in voclab.py
# records the measurement. Every stop leaves a TERMINATED cluster nothing will
# start again, which costs nothing to keep and buys nothing either.
#
# The default is cluster-stop, for anything that is not one of the two
# documented words: unset, empty, and unrecognized alike. It is the choice that
# errs on the side that can be undone. Reclaiming compute costs a student a
# cluster restart at worst, and the configuration and installed libraries
# survive it; deleting outright destroys anything the session was keeping and
# nothing brings it back. The alternative default, doing nothing, is the one
# that cannot be undone in the way that matters: a cluster left RUNNING bills
# until somebody notices, and the measurement in this file's header is what one
# of those looks like.
cleanup_command="cluster-stop"
case "$behavior_word" in
    [Ss][Tt][Oo][Pp])
        behavior_status="stop"
        voc_log "the student's data is preserved, so only the compute is reclaimed"
        ;;
    [Tt][Ee][Rr][Mm][Ii][Nn][Aa][Tt][Ee])
        behavior_status="terminate"
        cleanup_command="cluster-remove"
        voc_log "the environment reverts, so anything created for this session can go"
        ;;
    "")
        if [ "$behavior_arrived" = "yes" ]; then
            behavior_status="empty"
        else
            behavior_status="unset"
        fi
        voc_log "no end lab behavior ($behavior_status), so the compute is"
        voc_log "reclaimed and nothing is deleted"
        ;;
    *)
        behavior_status="unrecognized"
        voc_log "unrecognized behavior, so the compute is reclaimed and nothing"
        voc_log "is deleted"
        ;;
esac
voc_log "end lab behavior: [$behavior_raw] ($behavior_status), $cleanup_command"

# Two branches rather than three. Every ending now carries a cleanup command, so
# the only thing that can stop this hook reclaiming compute is not knowing which
# cluster to name.
if [ -z "$user_email" ]; then
    # The clusters are named after the student, so without an identity there is
    # no name to look up. Recorded rather than failed: the hook has nothing to
    # act on, which is a different thing from the action having gone wrong.
    voc_log "no VOC_DB_USER_EMAIL, so there is no per-student cluster to name"
    cleanup_error="MISSING_USER_EMAIL"
else
    voc_log "running $cleanup_command for $user_email"
    # Deliberately not voc_fail. Two reasons, and the first is the stronger. On a
    # terminate, Vocareum reverts the environment itself, and whether the
    # workspace is still reachable by the time this hook runs is not documented,
    # so a hook that failed the lab whenever this call failed would fail
    # routinely and teach everyone to ignore it. And a lab end that reports
    # failure is not something a student can act on; they have already left.
    #
    # So the failure is recorded instead, in the custom data, where
    # dbx-vocareum-diagnose reads it and where a leftover cluster becomes
    # traceable to the run that failed to reclaim it. voclab.py treats a cluster
    # that is already gone as success, so this fires on a real failure only.
    if voc_voclab "$cleanup_command" --user "$user_email"; then
        cluster_action="${voclab_cluster_action}"
        voc_log "cluster ${voclab_cluster_name}: $cluster_action"
    else
        cleanup_error="${voclab_error_code:-CLUSTER_CLEANUP_FAILED}"
        voc_log "cleanup failed, and the cluster may still be billing"
        voc_log "$cleanup_error: ${voclab_message:-no reason given}"
    fi
fi

# What user_setup.sh recorded, echoed back. This is the one place the two halves
# of a session can be matched up, and a mismatch means the lab was built by one
# run and torn down against another.
voc_log "custom data from the setup side: ${VOC_CUSTOM_DATA:-none}"

# end_lab_behavior is the value as it arrived and nothing else, so a reader sees
# what Vocareum really sent instead of inferring it from which branch ran. The
# two fields beside it are the interpretation, held separate for that reason:
# end_behavior_status says which of the five cases it fell into, and
# cleanup_command says what was actually asked of the workspace. The status is
# not called end_lab_behavior_status, because diagnose.py finds record fields by
# matching a fragment of the key path, and a name containing the other one would
# be picked up in its place on exactly the runs where the raw value is empty.
voc_custom_write "$(
    printf '%s, %s, %s, %s, %s, %s, %s, %s' \
        "$(voc_custom_field ran_at "$(date -u '+%Y-%m-%dT%H:%M:%SZ')")" \
        "$(voc_custom_field script "$VOC_SCRIPT_NAME")" \
        "$(voc_custom_field end_lab_behavior "$behavior_raw")" \
        "$(voc_custom_field end_behavior_status "$behavior_status")" \
        "$(voc_custom_field cleanup_command "$cleanup_command")" \
        "$(voc_custom_field user_email "${user_email:-unset}")" \
        "$(voc_custom_field cluster_action "$cluster_action")" \
        "$(voc_custom_field cleanup_error "${cleanup_error:-none}")"
)"

voc_log "done"
exit 0
