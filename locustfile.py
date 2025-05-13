# Copyright 2015-2015 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You may not use this file
# except in compliance with the License. A copy of the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is distributed on an "AS IS"
# BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under the License.

import json
import random
from locust import HttpUser, between, task
import locust
from websocket import create_connection
import ssl
import time
# https://dotabackseater.ruvice.com/

class HybridUser(HttpUser):
    def on_start(self):
        self.vote_session_started = False
        self.client.get(
            "config/40825038",
            headers={"Channel-Id": "40825038"}
        )
        # --- Setup WebSocket connection ---
        try:
            self.ws = create_connection(
                "wss://dotabackseater.ruvice.com/ws/40825038",  # Replace with your actual WSS URL
                sslopt={"cert_reqs": ssl.CERT_NONE}  # Disable cert verification (for testing only)
            )
            print("WebSocket connection success")
            # 🔥 Start WebSocket listening thread
            import threading
            threading.Thread(target=self._listen_ws, daemon=True).start()
        except Exception as e:
            print("WebSocket connection failed:", e)

    def on_stop(self):
        # --- Clean up WebSocket ---
        if hasattr(self, 'ws'):
            self.ws.close()
            print("Closed websocket connection")
    
    def _listen_ws(self):
        while True:
            try:
                msg = self.ws.recv()
                message = json.loads(msg)
                event_type = message.get("event")
                data = message.get("data")

                if event_type == "voteSession":
                    if data == "started":
                        print("Vote session started")
                        self.vote_session_started = True
                    else:
                        print("Vote session ended or paused")
                        self.vote_session_started = False
            except Exception as e:
                print("WebSocket listener error:", e)
                break

    @task
    def vote_hero_if_active(self):
        if not getattr(self, "vote_session_started", False):
            return  # Exit early if vote session not started
        randomId = random.randint(1, 100000)
        hero_id = random.randint(1, 139)
        self.client.post(
            "vote/hero/",
            headers={"Channel-Id": "40825038"},
            json={
                "channel_id": "40825038",
                "twitch_id": str(randomId),
                "hero_id": str(hero_id)
            }
        )