import sys
import os
# Add the project root to the module search path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest
from app import app, robots

@pytest.fixture
def client():
    with app.test_client() as client:
        # Clear any existing data
        robots.clear()
        yield client

def test_create_and_get_robot(client):
    # Create a new robot
    response = client.post('/api/robot', json={'name': 'Test Robot'})
    assert response.status_code == 201
    robot = response.get_json()
    assert 'id' in robot
    assert robot['name'] == 'Test Robot'
    # Base link must exist
    assert any(link['id'] == 'base' for link in robot['links'])
    
    # Get the robot by id
    response = client.get(f"/api/robot/{robot['id']}")
    assert response.status_code == 200
    fetched_robot = response.get_json()
    assert fetched_robot['id'] == robot['id']

def test_update_robot(client):
    # Create robot
    response = client.post('/api/robot', json={'name': 'Old Name'})
    robot = response.get_json()
    robot_id = robot['id']
    # Update robot
    response = client.put(f"/api/robot/{robot_id}", json={'name': 'New Name'})
    assert response.status_code == 202
    updated_robot = response.get_json()
    assert updated_robot['name'] == 'New Name'

def test_delete_robot(client):
    # Create robot
    response = client.post('/api/robot', json={'name': 'To Delete'})
    robot = response.get_json()
    robot_id = robot['id']
    # Delete robot
    response = client.delete(f"/api/robot/{robot_id}")
    assert response.status_code == 204
    # Ensure robot is deleted
    response = client.get(f"/api/robot/{robot_id}")
    assert response.status_code == 404

def test_create_link_and_joint(client):
    # Create a robot first
    response = client.post('/api/robot', json={'name': 'Robot With Link'})
    robot = response.get_json()
    robot_id = robot['id']
    # Create a new link with parentLinkId 'base'
    link_data = {
        'parentLinkId': 'base',
        'name': 'New Link',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    assert response.status_code == 201
    link = response.get_json()
    assert link['name'] == 'New Link'
    
    # Verify that a joint has been automatically created
    response = client.get(f"/api/robot/{robot_id}/joint")
    joints = response.get_json()
    assert any(j['childLinkId'] == link['id'] for j in joints)

def test_geometry_crud(client):
    # Create robot and link first
    response = client.post('/api/robot', json={'name': 'Robot Geometry'})
    robot = response.get_json()
    robot_id = robot['id']
    # Create a new link
    link_data = {
        'parentLinkId': 'base',
        'name': 'Geometry Link',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    link = response.get_json()
    link_id = link['id']
    
    # Create geometry
    geom_data = {
        'name': 'Test Box',
        'type': 'box',
        'extents': [1.0, 1.0, 1.0],
        'transform': [1,0,0,0,1,2,3]
    }
    response = client.post(f"/api/robot/{robot_id}/link/{link_id}/geometry", json=geom_data)
    assert response.status_code == 201
    geometry = response.get_json()
    geom_id = geometry['id']
    
    # Get geometry
    response = client.get(f"/api/robot/{robot_id}/link/{link_id}/geometry/{geom_id}")
    assert response.status_code == 200
    fetched_geom = response.get_json()
    assert fetched_geom['name'] == 'Test Box'
    
    # Update geometry
    response = client.put(f"/api/robot/{robot_id}/link/{link_id}/geometry/{geom_id}",
                          json={'name': 'Updated Box'})
    assert response.status_code == 202
    updated_geom = response.get_json()
    assert updated_geom['name'] == 'Updated Box'
    
    # Delete geometry
    response = client.delete(f"/api/robot/{robot_id}/link/{link_id}/geometry/{geom_id}")
    assert response.status_code == 204
    # Confirm deletion
    response = client.get(f"/api/robot/{robot_id}/link/{link_id}/geometry/{geom_id}")
    assert response.status_code == 404





def test_update_joint(client):
    # Create a robot and a link to auto-generate a joint
    response = client.post('/api/robot', json={'name': 'Joint Update Robot'})
    robot = response.get_json()
    robot_id = robot['id']
    # Create a new link with parentLinkId 'base' to auto-create a joint
    link_data = {
        'parentLinkId': 'base',
        'name': 'Link for Joint Update',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    link = response.get_json()
    # Get the joint that was created
    response = client.get(f"/api/robot/{robot_id}/joint")
    joints = response.get_json()
    joint = next((j for j in joints if j['childLinkId'] == link['id']), None)
    assert joint is not None

    # Update joint fields
    update_data = {
        'name': 'Updated Joint',
        'anchor': [0, 0, 1],
        'axis': [1, 0, 0]
    }
    response = client.put(f"/api/robot/{robot_id}/joint/{joint['id']}", json=update_data)
    assert response.status_code == 202
    updated_joint = response.get_json()
    assert updated_joint['name'] == 'Updated Joint'
    assert updated_joint['anchor'] == [0, 0, 1]
    assert updated_joint['axis'] == [1, 0, 0]

def test_update_link(client):
    # Create robot and a link
    response = client.post('/api/robot', json={'name': 'Robot For Link Update'})
    robot = response.get_json()
    robot_id = robot['id']
    link_data = {
        'parentLinkId': 'base',
        'name': 'Old Link Name',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    link = response.get_json()
    link_id = link['id']

    # Update the link
    update_data = {
        'name': 'New Link Name',
        'transform': [0,1,0,0,1,3,4]
    }
    response = client.put(f"/api/robot/{robot_id}/link/{link_id}", json=update_data)
    assert response.status_code == 202
    updated_link = response.get_json()
    assert updated_link['name'] == 'New Link Name'
    assert updated_link['transform'] == [0,1,0,0,1,3,4]

def test_delete_link_and_verify_joint_deletion(client):
    # Create robot and a link
    response = client.post('/api/robot', json={'name': 'Robot For Link Deletion'})
    robot = response.get_json()
    robot_id = robot['id']
    link_data = {
        'parentLinkId': 'base',
        'name': 'Link To Delete',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    link = response.get_json()
    link_id = link['id']

    # Ensure joint exists for this link
    response = client.get(f"/api/robot/{robot_id}/joint")
    joints = response.get_json()
    assert any(j['childLinkId'] == link_id for j in joints)

    # Delete the link
    response = client.delete(f"/api/robot/{robot_id}/link/{link_id}")
    assert response.status_code == 204

    # Verify that the joint associated with the deleted link is also removed
    response = client.get(f"/api/robot/{robot_id}/joint")
    joints = response.get_json()
    assert not any(j['childLinkId'] == link_id for j in joints)

def test_delete_base_link_error(client):
    # Create robot
    response = client.post('/api/robot', json={'name': 'Robot With Base Link'})
    robot = response.get_json()
    robot_id = robot['id']

    # Attempt to delete the base link
    response = client.delete(f"/api/robot/{robot_id}/link/base")
    # Expect a 400 error because base link should not be deletable
    assert response.status_code == 400

def test_invalid_parent_link(client):
    # Create a robot
    response = client.post('/api/robot', json={'name': 'Robot For Invalid Parent'})
    robot = response.get_json()
    robot_id = robot['id']

    # Attempt to create a link with a non-existent parentLinkId
    link_data = {
        'parentLinkId': 'nonexistent',
        'name': 'Invalid Link',
        'transform': [1,0,0,0,1,2,3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    # Expect a 404 error because the parent link doesn't exist
    assert response.status_code == 404

def test_get_nonexistent_robot(client):
    # Try to get a robot that doesn't exist
    response = client.get("/api/robot/nonexistent_robot")
    assert response.status_code == 404






def test_list_robots_empty(client):
    # When no robots exist, the list should be empty.
    response = client.get('/api/robot')
    assert response.status_code == 200
    data = response.get_json()
    assert data == []

def test_create_robot_default_name(client):
    # Creating a robot with an empty payload should use the default name.
    response = client.post('/api/robot', json={})
    assert response.status_code == 201
    robot = response.get_json()
    assert robot['name'] == 'Unnamed Robot'

def test_update_robot_nonexistent(client):
    # Updating a robot that doesn't exist should return 404.
    response = client.put('/api/robot/nonexistent', json={'name': 'New Name'})
    assert response.status_code == 404

def test_delete_robot_nonexistent(client):
    # Deleting a robot that doesn't exist should return 404.
    response = client.delete('/api/robot/nonexistent')
    assert response.status_code == 404

def test_list_joints_nonexistent(client):
    # Listing joints for a non-existent robot should return 404.
    response = client.get('/api/robot/nonexistent/joint')
    assert response.status_code == 404

def test_get_joint_nonexistent(client):
    # Create a robot and attempt to retrieve a non-existent joint.
    response = client.post('/api/robot', json={'name': 'Robot for Joint Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/joint/nonexistent')
    assert response.status_code == 404

def test_update_joint_nonexistent(client):
    # Create a robot and attempt to update a non-existent joint.
    response = client.post('/api/robot', json={'name': 'Robot for Joint Update Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(f'/api/robot/{robot_id}/joint/nonexistent', json={'name': 'Test'})
    assert response.status_code == 404

def test_list_links_nonexistent(client):
    # Listing links for a non-existent robot should return 404.
    response = client.get('/api/robot/nonexistent/link')
    assert response.status_code == 404

def test_get_link_nonexistent(client):
    # Create a robot and attempt to get a non-existent link.
    response = client.post('/api/robot', json={'name': 'Robot for Link Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/link/nonexistent')
    assert response.status_code == 404

def test_update_link_nonexistent(client):
    # Create a robot and attempt to update a non-existent link.
    response = client.post('/api/robot', json={'name': 'Robot for Link Update Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(
        f'/api/robot/{robot_id}/link/nonexistent',
        json={'name': 'New Name', 'transform': [0, 1, 0, 0, 1, 2, 3]}
    )
    assert response.status_code == 404

def test_delete_link_nonexistent(client):
    # Create a robot and attempt to delete a non-existent link.
    response = client.post('/api/robot', json={'name': 'Robot for Link Delete Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.delete(f'/api/robot/{robot_id}/link/nonexistent')
    assert response.status_code == 404

def test_create_link_missing_parent(client):
    # Create a robot and try to create a link without providing a parentLinkId.
    response = client.post('/api/robot', json={'name': 'Robot for Missing Parent'})
    robot = response.get_json()
    robot_id = robot['id']
    link_data = {
        'name': 'Link without Parent',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    }
    response = client.post(f'/api/robot/{robot_id}/link', json=link_data)
    assert response.status_code == 400

def test_list_geometries_nonexistent_robot(client):
    # Attempt to list geometries for a robot that doesn't exist.
    response = client.get('/api/robot/nonexistent/link/base/geometry')
    assert response.status_code == 404

def test_list_geometries_nonexistent_link(client):
    # Create a robot and try to list geometries for a non-existent link.
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Nonexistent Link'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/link/nonexistent/geometry')
    assert response.status_code == 404

def test_create_geometry_nonexistent_robot(client):
    # Attempt to create geometry for a non-existent robot.
    geom_data = {
        'name': 'Test Box',
        'type': 'box',
        'extents': [1.0, 1.0, 1.0],
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post('/api/robot/nonexistent/link/base/geometry', json=geom_data)
    assert response.status_code == 404

def test_create_geometry_nonexistent_link(client):
    # Create a robot and try to create geometry on a non-existent link.
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Nonexistent Link Creation'})
    robot = response.get_json()
    robot_id = robot['id']
    geom_data = {
        'name': 'Test Box',
        'type': 'box',
        'extents': [1.0, 1.0, 1.0],
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post(f'/api/robot/{robot_id}/link/nonexistent/geometry', json=geom_data)
    assert response.status_code == 404

def test_get_geometry_nonexistent(client):
    # Create a robot and link, then attempt to get a non-existent geometry.
    response = client.post('/api/robot', json={'name': 'Robot for Get Geometry Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.post(f'/api/robot/{robot_id}/link', json={
        'parentLinkId': 'base',
        'name': 'Link for Geometry',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    })
    link = response.get_json()
    link_id = link['id']
    response = client.get(f'/api/robot/{robot_id}/link/{link_id}/geometry/nonexistent')
    assert response.status_code == 404

def test_update_geometry_nonexistent(client):
    # Create a robot and link, then attempt to update a non-existent geometry.
    response = client.post('/api/robot', json={'name': 'Robot for Update Geometry Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.post(f'/api/robot/{robot_id}/link', json={
        'parentLinkId': 'base',
        'name': 'Link for Update Geometry',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    })
    link = response.get_json()
    link_id = link['id']
    response = client.put(f'/api/robot/{robot_id}/link/{link_id}/geometry/nonexistent', json={'name': 'New Name'})
    assert response.status_code == 404

def test_delete_geometry_nonexistent(client):
    # Create a robot and link, then attempt to delete a non-existent geometry.
    response = client.post('/api/robot', json={'name': 'Robot for Delete Geometry Nonexistent'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.post(f'/api/robot/{robot_id}/link', json={
        'parentLinkId': 'base',
        'name': 'Link for Delete Geometry',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.5],
        'axis': [0, 0, 1]
    })
    link = response.get_json()
    link_id = link['id']
    response = client.delete(f'/api/robot/{robot_id}/link/{link_id}/geometry/nonexistent')
    assert response.status_code == 404





# --- Error and Not-Found Tests ---

# ROBOT ERROR TESTS
def test_get_robot_nonexistent(client):
    response = client.get('/api/robot/nonexistent_robot')
    assert response.status_code == 404

def test_update_robot_nonexistent(client):
    response = client.put('/api/robot/nonexistent_robot', json={'name': 'Foo'})
    assert response.status_code == 404

def test_delete_robot_nonexistent(client):
    response = client.delete('/api/robot/nonexistent_robot')
    assert response.status_code == 404


# JOINT ERROR TESTS
def test_list_joints_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/joint')
    assert response.status_code == 404

def test_get_joint_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/joint/any')
    assert response.status_code == 404

def test_get_joint_nonexistent_joint(client):
    # Create a robot so that the robot exists but joint does not.
    response = client.post('/api/robot', json={'name': 'Robot for Joint Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/joint/nonexistent_joint')
    assert response.status_code == 404

def test_update_joint_nonexistent_robot(client):
    response = client.put('/api/robot/nonexistent_robot/joint/any', json={'name': 'Foo'})
    assert response.status_code == 404

def test_update_joint_nonexistent_joint(client):
    response = client.post('/api/robot', json={'name': 'Robot for Joint Update Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(f'/api/robot/{robot_id}/joint/nonexistent_joint', json={'name': 'Foo'})
    assert response.status_code == 404


# LINK ERROR TESTS
def test_list_links_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/link')
    assert response.status_code == 404

def test_create_link_nonexistent_robot(client):
    link_data = {
        'parentLinkId': 'base',
        'name': 'Test Link',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0],
        'axis': [0, 0, 1]
    }
    response = client.post('/api/robot/nonexistent_robot/link', json=link_data)
    assert response.status_code == 404

def test_create_link_missing_parentLinkId(client):
    # Create robot then try to create a link without parentLinkId.
    response = client.post('/api/robot', json={'name': 'Robot Missing Parent'})
    robot = response.get_json()
    robot_id = robot['id']
    link_data = {
        'name': 'Link without Parent',
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post(f'/api/robot/{robot_id}/link', json=link_data)
    assert response.status_code == 400

def test_create_link_nonexistent_parent(client):
    # Create robot then try to create a link with a non-existent parentLinkId.
    response = client.post('/api/robot', json={'name': 'Robot with Wrong Parent'})
    robot = response.get_json()
    robot_id = robot['id']
    link_data = {
        'parentLinkId': 'nonexistent',
        'name': 'Link with Invalid Parent',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0],
        'axis': [0, 0, 1]
    }
    response = client.post(f'/api/robot/{robot_id}/link', json=link_data)
    assert response.status_code == 404

def test_get_link_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/link/any')
    assert response.status_code == 404

def test_get_link_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Link Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/link/nonexistent_link')
    assert response.status_code == 404

def test_update_link_nonexistent_robot(client):
    response = client.put('/api/robot/nonexistent_robot/link/any', json={'name': 'Foo', 'transform': [1,0,0,0,1,2,3]})
    assert response.status_code == 404

def test_update_link_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Link Update Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(f'/api/robot/{robot_id}/link/nonexistent_link', json={'name': 'Foo', 'transform': [1,0,0,0,1,2,3]})
    assert response.status_code == 404

def test_delete_link_nonexistent_robot(client):
    response = client.delete('/api/robot/nonexistent_robot/link/any')
    assert response.status_code == 404

def test_delete_link_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Link Delete Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.delete(f'/api/robot/{robot_id}/link/nonexistent_link')
    assert response.status_code == 404


# GEOMETRY ERROR TESTS
def test_list_geometries_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/link/any/geometry')
    assert response.status_code == 404

def test_list_geometries_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry List'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/link/nonexistent_link/geometry')
    assert response.status_code == 404

def test_create_geometry_nonexistent_robot(client):
    geom_data = {
        'name': 'Test Geometry',
        'type': 'box',
        'extents': [1.0, 1.0, 1.0],
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post('/api/robot/nonexistent_robot/link/any/geometry', json=geom_data)
    assert response.status_code == 404

def test_create_geometry_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Creation'})
    robot = response.get_json()
    robot_id = robot['id']
    geom_data = {
        'name': 'Test Geometry',
        'type': 'box',
        'extents': [1.0, 1.0, 1.0],
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post(f'/api/robot/{robot_id}/link/nonexistent_link/geometry', json=geom_data)
    assert response.status_code == 404

def test_get_geometry_nonexistent_robot(client):
    response = client.get('/api/robot/nonexistent_robot/link/any/geometry/any')
    assert response.status_code == 404

def test_get_geometry_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Get'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.get(f'/api/robot/{robot_id}/link/nonexistent_link/geometry/any')
    assert response.status_code == 404

def test_get_geometry_nonexistent_geometry(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    # Use an existing link (the automatically created base link)
    response = client.get(f'/api/robot/{robot_id}/link/base/geometry/nonexistent_geometry')
    assert response.status_code == 404

def test_update_geometry_nonexistent_robot(client):
    response = client.put('/api/robot/nonexistent_robot/link/any/geometry/any', json={'name': 'Foo'})
    assert response.status_code == 404

def test_update_geometry_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Update'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(f'/api/robot/{robot_id}/link/nonexistent_link/geometry/any', json={'name': 'Foo'})
    assert response.status_code == 404

def test_update_geometry_nonexistent_geometry(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Update Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.put(f'/api/robot/{robot_id}/link/base/geometry/nonexistent_geometry', json={'name': 'Foo'})
    assert response.status_code == 404

def test_delete_geometry_nonexistent_robot(client):
    response = client.delete('/api/robot/nonexistent_robot/link/any/geometry/any')
    assert response.status_code == 404

def test_delete_geometry_nonexistent_link(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Delete'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.delete(f'/api/robot/{robot_id}/link/nonexistent_link/geometry/any')
    assert response.status_code == 404

def test_delete_geometry_nonexistent_geometry(client):
    response = client.post('/api/robot', json={'name': 'Robot for Geometry Delete Not Found'})
    robot = response.get_json()
    robot_id = robot['id']
    response = client.delete(f'/api/robot/{robot_id}/link/base/geometry/nonexistent_geometry')
    assert response.status_code == 404






def test_list_geometries_empty(client):
    """
    Create a new robot (which automatically creates a base link with no geometries)
    and verify that listing geometries on the base link returns an empty list.
    """
    # Create a new robot. The base link is created automatically with id 'base'
    response = client.post('/api/robot', json={'name': 'Test Robot'})
    assert response.status_code == 201
    robot = response.get_json()
    robot_id = robot['id']

    # List geometries for the base link (which should be empty)
    response = client.get(f"/api/robot/{robot_id}/link/base/geometry")
    assert response.status_code == 200
    geometries = response.get_json()
    # The base link's geometries list should be empty
    assert isinstance(geometries, list)
    assert len(geometries) == 0

def test_list_geometries_with_entry(client):
    """
    Create a new robot, add a geometry to the base link, and verify that the list_geometries
    endpoint returns a list containing the added geometry.
    """
    # Create a new robot.
    response = client.post('/api/robot', json={'name': 'Test Robot'})
    assert response.status_code == 201
    robot = response.get_json()
    robot_id = robot['id']

    # Add a new geometry to the base link
    geom_data = {
        'name': 'Test Geometry',
        'type': 'box',
        'extents': [1.0, 2.0, 3.0],
        'transform': [1, 0, 0, 0, 1, 2, 3]
    }
    response = client.post(f"/api/robot/{robot_id}/link/base/geometry", json=geom_data)
    assert response.status_code == 201

    # List geometries for the base link; now the list should contain one entry.
    response = client.get(f"/api/robot/{robot_id}/link/base/geometry")
    assert response.status_code == 200
    geometries = response.get_json()
    assert isinstance(geometries, list)
    assert len(geometries) == 1
    assert geometries[0]['name'] == 'Test Geometry'





def test_list_links_returns_base_link(client):
    """
    Create a new robot and verify that the GET /api/robot/{robotid}/link endpoint
    returns a list containing the automatically created base link.
    """
    # Create a new robot (base link is automatically added)
    response = client.post('/api/robot', json={'name': 'Test Robot'})
    assert response.status_code == 201
    robot = response.get_json()
    robot_id = robot['id']

    # Get the list of links for this robot
    response = client.get(f"/api/robot/{robot_id}/link")
    assert response.status_code == 200
    links = response.get_json()
    
    # Verify that the response is a list and contains at least the base link
    assert isinstance(links, list)
    assert len(links) >= 1
    assert any(link['id'] == 'base' for link in links)

def test_list_links_with_additional_link(client):
    """
    Create a new robot, add an additional link, and verify that the GET /api/robot/{robotid}/link 
    endpoint returns a list containing both the auto-created base link and the new link.
    """
    # Create a new robot
    response = client.post('/api/robot', json={'name': 'Robot With Multiple Links'})
    assert response.status_code == 201
    robot = response.get_json()
    robot_id = robot['id']

    # Create an additional link using the base link as parent
    link_data = {
        'parentLinkId': 'base',
        'name': 'Extra Link',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0],
        'axis': [0, 0, 1]
    }
    response = client.post(f"/api/robot/{robot_id}/link", json=link_data)
    assert response.status_code == 201

    # Retrieve the list of links for this robot
    response = client.get(f"/api/robot/{robot_id}/link")
    assert response.status_code == 200
    links = response.get_json()
    
    # There should be exactly 2 links: the base link and the extra link
    assert isinstance(links, list)
    assert len(links) == 2
    # Verify that one link is the base link and the other is the extra link
    assert any(link['id'] == 'base' for link in links)
    assert any(link['name'] == 'Extra Link' for link in links)





def test_get_joint_success(client):
    # Step 1: Create robot
    response = client.post('/api/robot', json={'name': 'Joint Fetch Robot'})
    robot = response.get_json()
    robot_id = robot['id']

    # Step 2: Create a link that auto-generates a joint
    link_data = {
        'parentLinkId': 'base',
        'name': 'Link A',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.2],
        'axis': [0, 0, 1]
    }
    response = client.post(f'/api/robot/{robot_id}/link', json=link_data)
    assert response.status_code == 201

    # Step 3: Get joint list and pick one to verify
    response = client.get(f'/api/robot/{robot_id}/joint')
    assert response.status_code == 200
    joints = response.get_json()
    assert len(joints) > 0
    joint = joints[0]
    joint_id = joint['id']

    # Step 4: Fetch joint by ID
    response = client.get(f'/api/robot/{robot_id}/joint/{joint_id}')
    assert response.status_code == 200
    fetched_joint = response.get_json()

    # Step 5: Verify content
    assert fetched_joint['id'] == joint['id']
    assert fetched_joint['name'] == joint['name']
    assert fetched_joint['parentLinkId'] == joint['parentLinkId']
    assert fetched_joint['childLinkId'] == joint['childLinkId']
    assert fetched_joint['anchor'] == joint['anchor']
    assert fetched_joint['axis'] == joint['axis']





def test_get_link_success(client):
    # Step 1: Create a robot
    response = client.post('/api/robot', json={'name': 'Robot with Link'})
    assert response.status_code == 201
    robot = response.get_json()
    robot_id = robot['id']

    # Step 2: Add a link to the robot
    link_data = {
        'parentLinkId': 'base',
        'name': 'Fetchable Link',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'anchor': [0, 0, 0.2],
        'axis': [0, 0, 1]
    }
    response = client.post(f'/api/robot/{robot_id}/link', json=link_data)
    assert response.status_code == 201
    new_link = response.get_json()
    link_id = new_link['id']

    # Step 3: Fetch the newly created link
    response = client.get(f'/api/robot/{robot_id}/link/{link_id}')
    assert response.status_code == 200
    fetched_link = response.get_json()

    # Step 4: Validate the content of the response
    assert fetched_link['id'] == new_link['id']
    assert fetched_link['name'] == 'Fetchable Link'
    assert fetched_link['parentLinkId'] == 'base'
    assert fetched_link['transform'] == [1, 0, 0, 0, 1, 2, 3]
    assert isinstance(fetched_link['geometries'], list)
    assert fetched_link['geometries'] == []  # Should be empty on creation
