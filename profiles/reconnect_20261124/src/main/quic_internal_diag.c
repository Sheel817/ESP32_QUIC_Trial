/* RECONNECT PROFILE: read-only access to ngtcp2 internal state for diagnostics.
 * Kept in its own file because the internal lib/ngtcp2_crypto.h and the public <ngtcp2/ngtcp2_crypto.h>
 * share one include guard and cannot be included together. Caller must hold quic_mutex. */
#include <stdio.h>
#include <ngtcp2/ngtcp2.h>
#include "ngtcp2_conn.h"
#include "ngtcp2_strm.h"

int quic_internal_diag(ngtcp2_conn *conn, int64_t stream_id, char *out, size_t size)
{
    int n = snprintf(out, size, " pto_count=%u lost_pending=%u", (unsigned)conn->cstat.pto_count,
                     (unsigned)conn->pktns.rtb.num_lost_pkts);
    if (n < 0 || (size_t)n >= size) return n;
    ngtcp2_strm *strm = stream_id >= 0 ? ngtcp2_conn_find_stream(conn, stream_id) : NULL;
    if (strm == NULL) {
        return n + snprintf(out + n, size - n, " stream=none");
    }
    return n + snprintf(out + n, size - n,
                        " stream=%lld tx_offset=%llu tx_cont_acked=%llu tx_loss_count=%u rx_last_offset=%llu rx_max_offset=%llu",
                        (long long)stream_id, (unsigned long long)strm->tx.offset,
                        (unsigned long long)strm->tx.cont_acked_offset, (unsigned)strm->tx.loss_count,
                        (unsigned long long)strm->rx.last_offset, (unsigned long long)strm->rx.max_offset);
}
