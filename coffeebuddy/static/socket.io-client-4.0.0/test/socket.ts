import * as expect from "expect.js";
import { io } from "..";

describe("socket", function () {
  this.timeout(70000);

  it("should have an accessible socket id equal to the server-side socket id (default namespace)", (done) => {
    const socket = io({ forceNew: true });

    socket.emit("getId", (id) => {
      expect(socket.id).to.be.ok();
      expect(socket.id).to.be.eql(id);
      expect(socket.id).to.not.eql(socket.io.engine.id);
      socket.disconnect();
      done();
    });
  });

  it("should have an accessible socket id equal to the server-side socket id (custom namespace)", (done) => {
    const socket = io("/foo", { forceNew: true });
    socket.emit("getId", (id) => {
      expect(socket.id).to.be.ok();
      expect(socket.id).to.be.eql(id);
      expect(socket.id).to.not.eql(socket.io.engine.id);
      socket.disconnect();
      done();
    });
  });

  it("clears socket.id upon disconnection", (done) => {
    const socket = io({ forceNew: true });
    socket.on("connect", () => {
      socket.on("disconnect", () => {
        expect(socket.id).to.not.be.ok();
        done();
      });

      socket.disconnect();
    });
  });

  it("doesn't fire an error event if we force disconnect in opening state", (done) => {
    const socket = io({ forceNew: true, timeout: 100 });
    socket.disconnect();
    socket.io.on("error", () => {
      throw new Error("Unexpected");
    });
    setTimeout(() => {
      done();
    }, 300);
  });

  it("fire a connect_error event when the connection cannot be established", (done) => {
    const socket = io("http://localhost:9823", {
      forceNew: true,
      timeout: 100,
    });
    socket.on("connect_error", () => {
      socket.close();
      done();
    });
  });

  it("doesn't fire a connect_error event when the connection is already established", (done) => {
    const socket = io({ forceNew: true });
    socket.on("connect", () => {
      socket.io.engine.close(true);
    });
    socket.on("connect_error", () => {
      done(new Error("should not happen"));
    });
    setTimeout(() => {
      socket.close();
      done();
    }, 300);
  });

  it("should change socket.id upon reconnection", (done) => {
    const socket = io({ forceNew: true });
    socket.on("connect", () => {
      const id = socket.id;

      socket.io.on("reconnect_attempt", () => {
        expect(socket.id).to.not.be.ok();
      });

      socket.io.on("reconnect", () => {
        expect(socket.id).to.not.eql(id);
        socket.disconnect();
        done();
      });

      socket.io.engine.close();
    });
  });

  it("should enable compression by default", (done) => {
    const socket = io({ forceNew: true });
    socket.on("connect", () => {
      socket.io.engine.once("packetCreate", (packet) => {
        expect(packet.options.compress).to.be(true);
        socket.disconnect();
        done();
      });
      socket.emit("hi");
    });
  });

  it("should disable compression", (done) => {
    const socket = io({ forceNew: true });
    socket.on("connect", () => {
      socket.io.engine.once("packetCreate", (packet) => {
        expect(packet.options.compress).to.be(false);
        socket.disconnect();
        done();
      });
      socket.compress(false).emit("hi");
    });
  });

  describe("query option", () => {
    it("should accept an object (default namespace)", (done) => {
      const socket = io("/", { forceNew: true, query: { e: "f" } });

      socket.emit("getHandshake", (handshake) => {
        expect(handshake.query.e).to.be("f");
        socket.disconnect();
        done();
      });
    });

    it("should accept a query string (default namespace)", (done) => {
      const socket = io("/?c=d", { forceNew: true });

      socket.emit("getHandshake", (handshake) => {
        expect(handshake.query.c).to.be("d");
        socket.disconnect();
        done();
      });
    });

    it("should accept an object", (done) => {
      const socket = io("/abc", { forceNew: true, query: { a: "b" } });

      socket.on("handshake", (handshake) => {
        expect(handshake.query.a).to.be("b");
        socket.disconnect();
        done();
      });
    });

    it("should accept a query string", (done) => {
      const socket = io("/abc?b=c&d=e", { forceNew: true });

      socket.on("handshake", (handshake) => {
        expect(handshake.query.b).to.be("c");
        expect(handshake.query.d).to.be("e");
        socket.disconnect();
        done();
      });
    });

    it("should properly encode the parameters", (done) => {
      const socket = io("/abc", { forceNew: true, query: { "&a": "&=?a" } });

      socket.on("handshake", (handshake) => {
        expect(handshake.query["&a"]).to.be("&=?a");
        socket.disconnect();
        done();
      });
    });
  });

  describe("auth option", () => {
    it("should accept an object", (done) => {
      const socket = io("/abc", { forceNew: true, auth: { a: "b", c: "d" } });

      socket.on("handshake", (handshake) => {
        expect(handshake.auth.a).to.be("b");
        expect(handshake.auth.c).to.be("d");
        expect(handshake.query.a).to.be(undefined);
        socket.disconnect();
        done();
      });
    });

    it("should accept an function", (done) => {
      const socket = io("/abc", {
        forceNew: true,
        auth: (cb) => cb({ e: "f" }),
      });

      socket.on("handshake", (handshake) => {
        expect(handshake.auth.e).to.be("f");
        expect(handshake.query.e).to.be(undefined);
        socket.disconnect();
        done();
      });
    });
  });

  it("should fire an error event on middleware failure from custom namespace", (done) => {
    const socket = io("/no", { forceNew: true });
    socket.on("connect_error", (err) => {
      expect(err).to.be.an(Error);
      expect(err.message).to.eql("Auth failed (custom namespace)");
      socket.disconnect();
      done();
    });
  });

  it("should throw on reserved event", () => {
    const socket = io("/no", { forceNew: true });

    expect(() => socket.emit("disconnecting", "goodbye")).to.throwException(
      /"disconnecting" is a reserved event name/
    );
  });

  describe("volatile packets", () => {
    it("should discard a volatile packet when the socket is not connected", (done) => {
      const socket = io({ forceNew: true, autoConnect: false });

      socket.volatile.emit("getId", () => {
        done(new Error("should not happen"));
      });

      socket.emit("getId", () => {
        socket.disconnect();
        done();
      });

      socket.connect();
    });

    it("should discard a volatile packet when the pipe is not ready", (done) => {
      const socket = io({ forceNew: true });

      socket.on("connect", () => {
        socket.emit("getId", () => {
          socket.disconnect();
          done();
        });

        socket.volatile.emit("getId", () => {
          done(new Error("should not happen"));
        });
      });
    });

    it("should send a volatile packet when the socket is connected and the pipe is ready", (done) => {
      const socket = io({ forceNew: true });

      const interval = setInterval(() => {
        socket.volatile.emit("getId", () => {
          clearInterval(interval);
          socket.disconnect();
          done();
        });
      }, 200);
    });
  });

  describe("onAny", () => {
    it("should call listener", (done) => {
      const socket = io("/abc");

      socket.onAny((event, arg1) => {
        expect(event).to.be("handshake");
        expect(arg1).to.be.an(Object);
        done();
      });
    });

    it("should prepend listener", (done) => {
      const socket = io("/abc");

      let count = 0;

      socket.onAny((event, arg1) => {
        expect(count).to.be(2);
        done();
      });

      socket.prependAny(() => {
        expect(count++).to.be(1);
      });

      socket.prependAny(() => {
        expect(count++).to.be(0);
      });
    });

    it("should remove listener", (done) => {
      const socket = io("/abc");

      let count = 0;

      const fail = () => done(new Error("fail"));

      socket.onAny(fail);
      socket.offAny(fail);
      expect(socket.listenersAny.length).to.be(0);

      socket.onAny(() => {
        done();
      });
    });
  });
});
