extern "C" {
#include <breakwater/breakwater.h>
#include <breakwater/seda.h>
#include <breakwater/dagor.h>
#include <breakwater/nocontrol.h>
}

#include "breakwater/rpc++.h"
#include "cc/net.h"
#include "cc/runtime.h"


#include "cc/sync.h"

#include <memory>

netaddr server;
const struct crpc_ops *crpc_ops;
const struct srpc_ops *srpc_ops;

int StringToAddr(const char *str, uint32_t *addr) {
    uint8_t a, b, c, d;

    if (sscanf(str, "%hhu.%hhu.%hhu.%hhu", &a, &b, &c, &d) != 4) return -EINVAL;

    *addr = MAKE_IP_ADDR(a, b, c, d);
    return 0;
}

void ClientHandler(void *arg) {
    struct rpc_session_info info = {.session_type = 0};
    std::unique_ptr<rpc::RpcClient> conn(rpc::RpcClient::Dial(server, 1, nullptr, nullptr, &info));
    const char *message = "hello";
    auto ret = conn->Send(message, 5, 8423, nullptr);
    if (ret == -ENOBUFS)
        return;
    if (ret != static_cast<ssize_t>(5))
        return; //panic("write failed, ret = %ld", ret);
}

int main(int argc, char *argv[]) {

    rt::Mutex sendMutex_;
    // usage: client [server_ip] [# threads/conns] [config]
    if (argc < 4) {
        fprintf(stderr, "Usage: %s client <server_ip> <# threads/conns> <config>\n", argv[0]);
        return -EINVAL;
    }


    std::string user = argv[1];
    crpc_ops = &cbw_ops;
    srpc_ops = &sbw_ops;
    if (user.compare("client") == 0) {
        auto ret = StringToAddr(argv[2], &server.ip);
        if (ret)
            return -EINVAL;
        server.port = 8001;
        runtime_init(argv[4], ClientHandler, NULL);
    }
}