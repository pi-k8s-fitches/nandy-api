import unittest
import unittest.mock

import os
import copy
import json
import yaml

import nandy.store.graphite
import nandy.store.redis
import nandy.store.mysql

import service

class TestService(unittest.TestCase):

    maxDiff = None

    @classmethod
    @unittest.mock.patch("graphyte.Sender", nandy.store.graphite.MockGraphyteSender)
    @unittest.mock.patch("redis.StrictRedis", nandy.store.redis.MockRedis) 
    def setUpClass(cls):

        cls.app = service.app()
        cls.data = cls.app.app.data
        cls.api = cls.app.app.test_client()

    def setUp(self):

        nandy.store.mysql.create_database()

        self.sample = nandy.store.mysql.Sample(self.data.mysql.session)

        nandy.store.mysql.Base.metadata.create_all(self.data.mysql.engine)

    def tearDown(self):

        self.data.mysql.session.close()

    def assertStatusValue(self, response, code, key, value):

        self.assertEqual(response.status_code, code, response.json)
        self.assertEqual(response.json[key], value)

    def assertStatusModel(self, response, code, key, model):

        self.assertEqual(response.status_code, code, response.json)

        for field in model:
            self.assertEqual(response.json[key][field], model[field])

    def assertStatusModels(self, response, code, key, models):

        self.assertEqual(response.status_code, code, response.json)

        for index, model in enumerate(models):
            for field in model:
                self.assertEqual(response.json[key][index][field], model[field])

    def test_model_in(self):

        self.assertEqual(service.model_in({
            "a": 1,
            "yaml": yaml.dump({"b": 2})
        }), {
            "a": 1,
            "data": {
                "b": 2
            }
        })

    def test_model_out(self):

        area = self.sample.area(
            name="a", 
            status="b", 
            updated=3,
            data={"d": 4}
        )

        self.assertEqual(service.model_out(area), {
            "area_id": area.area_id,
            "name": "a",
            "status": "b",
            "updated": 3,
            "data": {
                "d": 4
            },
            "yaml": yaml.dump({"d": 4}, default_flow_style=False)
        })

    def test_models_out(self):

        area = self.sample.area(
            name="a", 
            status="b", 
            updated=3,
            data={"d": 4}
        )

        self.assertEqual(service.models_out([area]), [{
            "area_id": area.area_id,
            "name": "a",
            "status": "b",
            "updated": 3,
            "data": {
                "d": 4
            },
            "yaml": yaml.dump({"d": 4}, default_flow_style=False)
        }])

    def test_setting_load(self):

        self.assertEqual(service.setting_load(), {
            "node": [
                "pi-k8s-timmy",
                "pi-k8s-sally"
            ],
            "language": [
                "en"
            ]
        })

    def test_health(self):

        self.assertEqual(self.api.get("/health").json, {"message": "OK"})

    def test_setting_list(self):

        response = self.api.get("/setting")

        self.assertEqual(response.json, {
            "settings": {
                "node": [
                    "pi-k8s-timmy",
                    "pi-k8s-sally"
                ],
                "language": [
                    "en"
                ]
            }
        })
        self.assertEqual(response.status_code, 200)

    # Person

    def test_person_create(self):

        self.assertStatusModel(self.api.post("/person", json={
            "person": {
                "name": "unit",
                "email": "test"
            }
        }), 201, "person", {
            "name": "unit",
            "email": "test",
        })

    def test_person_list(self):

        self.sample.person("unit")
        self.sample.person("test")

        self.assertStatusModels(self.api.get("/person"), 200, "persons", [
            {
                "name": "test"
            },
            {
                "name": "unit"
            }
        ])
        
    def test_person_retrieve(self):

        sample = self.sample.person("unit", "test")

        self.assertStatusModel(self.api.get(f"/person/{sample.person_id}"), 200, "person", {
            "name": "unit",
            "email": "test",
        })

    def test_person_update(self):

        sample = self.sample.person("unit", "test")

        self.assertStatusValue(self.api.patch(f"/person/{sample.person_id}", json={
            "person": {
                "email": "testy"
            }
        }), 202, "updated", 1)

        queried = self.data.mysql.session.query(nandy.store.mysql.Person).one()
        self.assertEqual(queried.email, "testy")

    def test_person_delete(self):

        sample = self.sample.person("unit", "test")

        self.assertStatusValue(self.api.delete(f"/person/{sample.person_id}"), 202, "deleted", 1)

        self.assertEqual(len(self.data.mysql.session.query(nandy.store.mysql.Person).all()), 0)

    # Area

    def test_area_create(self):

        self.assertStatusModel(self.api.post("/area", json={
            "area": {
                "name": "unit",
                "status": "test",
                "updated": 7,
                "data": {"a": 1}
            }
        }), 201, "area", {
            "name": "unit",
            "status": "test",
            "updated": 7,
            "data": {"a": 1},
            "yaml": yaml.dump({"a": 1}, default_flow_style=False)
        })

    def test_area_list(self):

        self.sample.area("unit")
        self.sample.area("test")

        self.assertStatusModels(self.api.get("/area"), 200, "areas", [
            {
                "name": "test"
            },
            {
                "name": "unit"
            }
        ])
        
    def test_area_retrieve(self):

        sample = self.sample.area(name="unit", status="test", updated=7, data={"a": 1})

        self.assertStatusModel(self.api.get(f"/area/{sample.area_id}"), 200, "area", {
            "name": "unit",
            "status": "test",
            "updated": 7,
            "data": {"a": 1},
            "yaml": yaml.dump({"a": 1}, default_flow_style=False)
        })

    def test_area_update(self):

        sample = self.sample.area(name="unit", status="test")

        self.assertStatusValue(self.api.patch(f"/area/{sample.area_id}", json={
            "area": {
                "status": "testy"
            }
        }), 202, "updated", 1)

        queried = self.data.mysql.session.query(nandy.store.mysql.Area).one()
        self.assertEqual(queried.status, "testy")

    def test_area_status(self):

        person = self.sample.person("kid")
        area = self.sample.area(
            name="changing", 
            status="test", 
            updated=7, 
            data={
                "statuses": [
                    {
                        "value": "test",
                        "chore": {
                            "person": "kid",
                            "name": 'nope',
                            "node": "test",
                            "text": "chore it",
                            "language": "en-us",
                            "tasks": [
                                {
                                    "text": "do it"
                                }
                            ]
                        }
                    },
                    {
                        "value": "unit",
                        "chore": {
                            "person": "kid",
                            "name": 'yep',
                            "node": "test",
                            "text": "chore it",
                            "language": "en-us",
                            "tasks": [
                                {
                                    "text": "do it"
                                }
                            ]
                        }
                    }
                ]
            }
        )
        self.data.mysql.session.add(area)
        self.data.mysql.session.commit()

        self.assertStatusValue(self.api.post(f"/area/{area.area_id}/test"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/area/{area.area_id}/unit"), 202, "updated", 1)

        updated = self.data.mysql.session.query(nandy.store.mysql.Area).one()
        self.assertEqual(updated.status, "unit")

        chore = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(chore.name, "yep")

    def test_area_delete(self):

        sample = self.sample.area("unit")

        self.assertStatusValue(self.api.delete(f"/area/{sample.area_id}"), 202, "deleted", 1)

        self.assertEqual(len(self.data.mysql.session.query(nandy.store.mysql.Area).all()), 0)

    # Template

    def test_template_create(self):

        self.assertStatusModel(self.api.post("/template", json={
            "template": {
                "name": "unit",
                "kind": "chore",
                "data": {"a": 1}
            }
        }), 201, "template", {
            "name": "unit",
            "kind": "chore",
            "data": {"a": 1},
            "yaml": yaml.dump({"a": 1}, default_flow_style=False)
        })

    def test_template_list(self):

        self.sample.template(name="unit", kind="chore")
        self.sample.template(name="test", kind="act")

        self.assertStatusModels(self.api.get("/template"), 200, "templates", [
            {
                "name": "test"
            },
            {
                "name": "unit"
            }
        ])
      
    def test_template_retrieve(self):

        sample = self.sample.template(name="unit", kind="chore", data={"a": 1})

        self.assertStatusModel(self.api.get(f"/template/{sample.template_id}"), 200, "template", {
            "name": "unit",
            "data": {"a": 1},
            "yaml": yaml.dump({"a": 1}, default_flow_style=False)
        })

    def test_template_update(self):

        sample = self.sample.template(name="unit", kind="chore")

        self.assertStatusValue(self.api.patch(f"/template/{sample.template_id}", json={
            "template": {
                "kind": "act"
            }
        }), 202, "updated", 1)

        queried = self.data.mysql.session.query(nandy.store.mysql.Template).one()
        self.assertEqual(queried.kind, "act")

    def test_template_delete(self):

        sample = self.sample.template(name="unit", kind="chore")

        self.assertStatusValue(self.api.delete(f"/template/{sample.template_id}"), 202, "deleted", 1)

        self.assertEqual(len(self.data.mysql.session.query(nandy.store.mysql.Template).all()), 0)

    # Chore

    @unittest.mock.patch("nandy.data.time.time")
    def test_chore_create(self, mock_time):

        mock_time.return_value = 7

        person = self.sample.person("kid")

        self.assertStatusModel(self.api.post("/chore", json={
            "template": {
                "person": "kid",
                "name": 'Unit',
                "node": "test",
                "text": "chore it",
                "language": "en-us",
                "tasks": [
                    {
                        "text": "do it"
                    }
                ]
            }
        }), 201, "chore", {
            "person_id": person.person_id,
            "name": "Unit",
            "status": "started",
            "created": 7,
            "updated": 7,
            "data": {
                "person": "kid",
                "name": 'Unit',
                "node": "test",
                "text": "chore it",
                "language": "en-us",
                "start": 7,
                "notified": 7,
                "updated": 7,
                "tasks": [
                    {
                        "id": 0,
                        "text": "do it",
                        "start": 7,
                        "notified": 7
                    }
                ]
            },
            "yaml": yaml.dump({
                "person": "kid",
                "name": 'Unit',
                "node": "test",
                "text": "chore it",
                "language": "en-us",
                "start": 7,
                "notified": 7,
                "updated": 7,
                "tasks": [
                    {
                        "id": 0,
                        "text": "do it",
                        "start": 7,
                        "notified": 7
                    }
                ]
            }, default_flow_style=False)
        })

        # No template or tasks

        self.assertStatusModel(self.api.post("/chore", json={
            "chore": {
                "person_id": person.person_id,
                "name": 'Test',
                "data": {
                    "node": "test",
                    "text": "chore it"
                }
            }
        }), 201, "chore", {
            "person_id": person.person_id,
            "name": "Test",
            "status": "started",
            "created": 7,
            "updated": 7,
            "data": {
                "node": "test",
                "text": "chore it",
                 "language": "en-us",
                "start": 7,
                "notified": 7,
                "updated": 7,
            },
            "yaml": yaml.dump({
                "node": "test",
                "text": "chore it",
                 "language": "en-us",
                "start": 7,
                "notified": 7,
                "updated": 7,
            }, default_flow_style=False)
        })

    def test_chore_list(self):

        self.sample.chore(person="unit", name="Unit", created=7)
        self.sample.chore(person="test", name="Test", created=8)

        self.assertStatusModels(self.api.get("/chore"), 200, "chores", [
            {
                "name": "Test"
            },
            {
                "name": "Unit"
            }
        ])

    def test_chore_retrieve(self):

        sample = self.sample.chore(person="unit", name="Unit", data={
            "language": "en-us",
            "text": "Test"
        })

        self.assertStatusModel(self.api.get(f"/chore/{sample.chore_id}"), 200, "chore", {
            "name": "Unit",
            "data": {
                "language": "en-us",
                "text": "Test"
            },
            "yaml": yaml.dump({
                "language": "en-us",
                "text": "Test"
            }, default_flow_style=False)
        })

    def test_chore_update(self):

        sample = self.sample.chore(person="unit", name="Test")

        self.assertStatusValue(self.api.patch(f"/chore/{sample.chore_id}", json={
            "chore": {
                "name": "Unit"
            }
        }), 202, "updated", 1)

        queried = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(queried.name, "Unit")

    @unittest.mock.patch("nandy.data.time.time")
    def test_chore_action(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample.chore(person="kid", name="Unit", data={"start": 1}, tasks=[
            {
                "start": 2,                        
                "text": "do it"
            },
            {
                "text": "hold it"
            }
        ])

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/next"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/pause"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": True,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/pause"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/unpause"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": False,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/unpause"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/skip"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "paused": False,
            "skipped": True,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/skip"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/unskip"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": False,
            "skipped": False,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/unskip"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/complete"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "paused": False,
            "skipped": False,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/complete"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/incomplete"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "paused": False,
            "skipped": False,
            "tasks": [
                {
                    "start": 2,
                    "end": 7,
                    "notified": 7,
                    "text": "do it"
                },
                {
                    "start": 7,
                    "notified": 7,
                    "text": "hold it"
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/incomplete"), 202, "updated", 0)

    def test_chore_delete(self):

        sample = self.sample.chore(person="kid")

        self.assertStatusValue(self.api.delete(f"/chore/{sample.chore_id}"), 202, "deleted", 1)

        self.assertEqual(len(self.data.mysql.session.query(nandy.store.mysql.Chore).all()), 0)

    # Task

    @unittest.mock.patch("nandy.data.time.time")
    def test_task_action(self, mock_time):

        mock_time.return_value = 7

        chore = self.sample.chore(person="kid", data={"start": 1}, tasks=[{"text": "do it", "start": 1}])

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/pause"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "notified": 7,
                    "text": "do it",
                    "paused": True
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/pause"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/unpause"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "notified": 7,
                    "text": "do it",
                    "paused": False
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/unpause"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/skip"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "end": 7,
                    "notified": 7,
                    "text": "do it",
                    "paused": False,
                    "skipped": True
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/skip"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/unskip"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "notified": 7,
                    "text": "do it",
                    "paused": False,
                    "skipped": False
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/unskip"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/complete"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "end": 7,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "end": 7,
                    "notified": 7,
                    "text": "do it",
                    "paused": False,
                    "skipped": False
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/complete"), 202, "updated", 0)

        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/incomplete"), 202, "updated", 1)
        updated = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(dict(updated.data), {
            "text": "chore it",
            "language": "en-us",
            "start": 1,
            "notified": 7,
            "updated": 7,
            "tasks": [
                {
                    "start": 1,
                    "notified": 7,
                    "text": "do it",
                    "paused": False,
                    "skipped": False
                }
            ]
        })
        self.assertStatusValue(self.api.post(f"/chore/{chore.chore_id}/task/0/incomplete"), 202, "updated", 0)

    # Act

    @unittest.mock.patch("nandy.data.time.time")
    def test_act_create(self, mock_time):

        mock_time.return_value = 7

        person = self.sample.person("unit")

        self.assertStatusModel(self.api.post("/act", json={
            "template": {
                "person": "unit",
                "name": 'Unit',
                "value": "negative",
                "chore": {
                    "name": "Test",
                    "text": "chore it",
                    "node": "bump"
                }
            }
        }), 201, "act", {
            "person_id": person.person_id,
            "name": "Unit",
            "created": 7,
            "value": "negative",
            "data": {
                "person": "unit",
                "name": 'Unit',
                "value": "negative",
                "chore": {
                    "name": "Test",
                    "text": "chore it",
                    "node": "bump"
                }
            },
            "yaml": yaml.dump({
                "person": "unit",
                "name": 'Unit',
                "value": "negative",
                "chore": {
                    "name": "Test",
                    "text": "chore it",
                    "node": "bump"
                }
            }, default_flow_style=False)
        })

        chore = self.data.mysql.session.query(nandy.store.mysql.Chore).one()
        self.assertEqual(chore.person_id, person.person_id)
        self.assertEqual(chore.name, "Test")

        self.assertStatusModel(self.api.post("/act", json={
            "act": {
                "person_id": person.person_id,
                "name": 'Unit',
                "value": "positive",
                "data": {}
            }
        }), 201, "act", {
                "person_id": person.person_id,
                "name": 'Unit',
                "value": "positive",
            "created": 7
        })

    def test_act_list(self):

        self.sample.act(person="unit", name="Unit", created=7)
        self.sample.act(person="test", name="Test", created=8)

        self.assertStatusModels(self.api.get("/act"), 200, "acts", [
            {
                "name": "Test"
            },
            {
                "name": "Unit"
            }
        ])

    def test_act_retrieve(self):

        sample = self.sample.act(person="kid", name='Unit', value="positive", created=7, data={"a": 1})

        self.assertStatusModel(self.api.get(f"/act/{sample.act_id}"), 200, "act", {
            "name": "Unit",
            "data": {
                "a": 1
            },
            "yaml": yaml.dump({
                "a": 1
            }, default_flow_style=False)
        })

    def test_act_update(self):

        sample = self.sample.act(person="kid", name='Unit')

        self.assertStatusValue(self.api.patch(f"/act/{sample.act_id}", json={
            "act": {
                "name": "Test"
            }
        }), 202, "updated", 1)

        queried = self.data.mysql.session.query(nandy.store.mysql.Act).one()
        self.assertEqual(queried.name, "Test")

    def test_act_delete(self):

        sample = self.sample.act(person="kid", name='Unit')

        self.assertStatusValue(self.api.delete(f"/act/{sample.act_id}"), 202, "deleted", 1)

        self.assertEqual(len(self.data.mysql.session.query(nandy.store.mysql.Act).all()), 0)
