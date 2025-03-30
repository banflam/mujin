from flask import Flask, request, jsonify, abort, make_response
import uuid

app = Flask(__name__)

# In-memory storage
robots = {}  
# { robot_id: { 'id': ..., 'name': ..., 'links': [], 'joints': [] } }

# Helpers to generate IDs
def generate_robot_id():
    return "robot" + str(uuid.uuid4())[:8]

def generate_joint_id():
    return "j" + str(uuid.uuid4())[:8]

def generate_link_id():
    return "link" + str(uuid.uuid4())[:8]

def generate_geometry_id():
    return "geom" + str(uuid.uuid4())[:8]

# -----------------------------
# Robot APIs
# -----------------------------
@app.route('/api/robot', methods=['GET'])
def list_robots():
    return jsonify(list(robots.values())), 200

@app.route('/api/robot', methods=['POST'])
def create_robot():
    data = request.get_json() or {}
    robot_id = generate_robot_id()
    robot = {
        'id': robot_id,
        'name': data.get('name', 'Unnamed Robot'),
        'links': [],
        'joints': []
    }
    # Automatically create base link
    base_link = {
        'id': 'base',
        'parentLinkId': None,
        'name': 'Base Link',
        'transform': [1, 0, 0, 0, 1, 2, 3],
        'geometries': []
    }
    robot['links'].append(base_link)
    robots[robot_id] = robot
    return jsonify(robot), 201

@app.route('/api/robot/<robotid>', methods=['GET'])
def get_robot(robotid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    return jsonify(robot), 200

@app.route('/api/robot/<robotid>', methods=['PUT'])
def update_robot(robotid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    data = request.get_json() or {}
    # Only update mutable properties
    robot['name'] = data.get('name', robot['name'])
    return jsonify(robot), 202

@app.route('/api/robot/<robotid>', methods=['DELETE'])
def delete_robot(robotid):
    if robotid not in robots:
        abort(404)
    del robots[robotid]
    return '', 204

# -----------------------------
# Joint APIs
# -----------------------------
@app.route('/api/robot/<robotid>/joint', methods=['GET'])
def list_joints(robotid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    return jsonify(robot.get('joints', [])), 200

@app.route('/api/robot/<robotid>/joint/<jointid>', methods=['GET'])
def get_joint(robotid, jointid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    joint = next((j for j in robot.get('joints', []) if j['id'] == jointid), None)
    if not joint:
        abort(404)
    return jsonify(joint), 200

@app.route('/api/robot/<robotid>/joint/<jointid>', methods=['PUT'])
def update_joint(robotid, jointid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    joint = next((j for j in robot.get('joints', []) if j['id'] == jointid), None)
    if not joint:
        abort(404)
    data = request.get_json() or {}
    # Allow update of mutable fields (here only name, anchor, axis are assumed mutable)
    joint['name'] = data.get('name', joint['name'])
    joint['anchor'] = data.get('anchor', joint['anchor'])
    joint['axis'] = data.get('axis', joint['axis'])
    return jsonify(joint), 202

# -----------------------------
# Link APIs
# -----------------------------
@app.route('/api/robot/<robotid>/link', methods=['GET'])
def list_links(robotid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    return jsonify(robot.get('links', [])), 200

@app.route('/api/robot/<robotid>/link', methods=['POST'])
def create_link(robotid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    data = request.get_json() or {}
    parent_link_id = data.get('parentLinkId')
    if not parent_link_id:
        abort(400, "parentLinkId is required")
    # Verify parent link exists
    parent_link = next((l for l in robot['links'] if l['id'] == parent_link_id), None)
    if not parent_link:
        abort(404, "Parent link not found")
    link_id = generate_link_id()
    new_link = {
        'id': link_id,
        'parentLinkId': parent_link_id,
        'name': data.get('name', 'Unnamed Link'),
        'transform': data.get('transform', [1, 0, 0, 0, 1, 2, 3]),
        'geometries': []
    }
    robot['links'].append(new_link)
    # Automatically create a joint connecting the parent link to the new link
    joint = {
        'id': generate_joint_id(),
        'name': f"Joint between {parent_link_id} and {link_id}",
        'parentLinkId': parent_link_id,
        'childLinkId': link_id,
        'anchor': data.get('anchor', [0, 0, 0]),
        'axis': data.get('axis', [0, 0, 1])
    }
    robot.setdefault('joints', []).append(joint)
    return jsonify(new_link), 201

@app.route('/api/robot/<robotid>/link/<linkid>', methods=['GET'])
def get_link(robotid, linkid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    return jsonify(link), 200

@app.route('/api/robot/<robotid>/link/<linkid>', methods=['PUT'])
def update_link(robotid, linkid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    data = request.get_json() or {}
    # Update mutable fields (e.g., name and transform)
    link['name'] = data.get('name', link['name'])
    link['transform'] = data.get('transform', link['transform'])
    return jsonify(link), 202

@app.route('/api/robot/<robotid>/link/<linkid>', methods=['DELETE'])
def delete_link(robotid, linkid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    # Do not allow deletion of base link
    if linkid == 'base':
        abort(400, "Base link cannot be deleted")
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    robot['links'].remove(link)
    # Remove associated joint(s)
    robot['joints'] = [j for j in robot.get('joints', []) if j['childLinkId'] != linkid]
    return '', 204

# -----------------------------
# Geometry APIs
# -----------------------------
@app.route('/api/robot/<robotid>/link/<linkid>/geometry', methods=['GET'])
def list_geometries(robotid, linkid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    return jsonify(link.get('geometries', [])), 200

@app.route('/api/robot/<robotid>/link/<linkid>/geometry', methods=['POST'])
def create_geometry(robotid, linkid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    data = request.get_json() or {}
    geom_id = generate_geometry_id()
    geometry = {
        'id': geom_id,
        'name': data.get('name', 'Unnamed Geometry'),
        'type': data.get('type', 'box'),
        'extents': data.get('extents', [1.0, 1.0, 1.0]),
        'transform': data.get('transform', [1, 0, 0, 0, 1, 2, 3])
    }
    link.setdefault('geometries', []).append(geometry)
    return jsonify(geometry), 201

@app.route('/api/robot/<robotid>/link/<linkid>/geometry/<geometryid>', methods=['GET'])
def get_geometry(robotid, linkid, geometryid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    geometry = next((g for g in link.get('geometries', []) if g['id'] == geometryid), None)
    if not geometry:
        abort(404)
    return jsonify(geometry), 200

@app.route('/api/robot/<robotid>/link/<linkid>/geometry/<geometryid>', methods=['PUT'])
def update_geometry(robotid, linkid, geometryid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    geometry = next((g for g in link.get('geometries', []) if g['id'] == geometryid), None)
    if not geometry:
        abort(404)
    data = request.get_json() or {}
    geometry['name'] = data.get('name', geometry['name'])
    geometry['extents'] = data.get('extents', geometry['extents'])
    geometry['transform'] = data.get('transform', geometry['transform'])
    return jsonify(geometry), 202

@app.route('/api/robot/<robotid>/link/<linkid>/geometry/<geometryid>', methods=['DELETE'])
def delete_geometry(robotid, linkid, geometryid):
    robot = robots.get(robotid)
    if not robot:
        abort(404)
    link = next((l for l in robot.get('links', []) if l['id'] == linkid), None)
    if not link:
        abort(404)
    geometry = next((g for g in link.get('geometries', []) if g['id'] == geometryid), None)
    if not geometry:
        abort(404)
    link['geometries'].remove(geometry)
    return '', 204

if __name__ == '__main__':
    app.run(debug=True)
