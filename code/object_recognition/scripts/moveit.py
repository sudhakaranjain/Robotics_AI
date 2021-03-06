import rospy
import moveit_commander
from moveit_commander import MoveGroupCommander, PlanningSceneInterface
from moveit_msgs.msg import PlanningScene, ObjectColor, Grasp, GripperTranslation, MoveItErrorCodes
from tf.transformations import quaternion_from_euler, euler_from_quaternion
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from geometry_msgs.msg import PoseStamped, Pose, TransformStamped
from std_srvs.srv import Empty
import tf

import sys
import math 
import numpy as np

class MoveIt(object):
    
    def __init__(self):        
        moveit_commander.roscpp_initialize(sys.argv)
        self.scene = PlanningSceneInterface()
        self.clear_octomap = rospy.ServiceProxy("/clear_octomap", Empty)
        
        self.arm = MoveGroupCommander("arm")
        self.gripper = MoveGroupCommander("gripper")
        
        # already default
        self.arm.set_planner_id("RRTConnectkConfigDefault")
               
        self.end_effector_link = self.arm.get_end_effector_link()
        
        self.arm.allow_replanning(True)
        self.arm.set_planning_time(5)
        
        self.transformer = tf.TransformListener()
        
        rospy.sleep(2) # allow some time for initialization of moveit
        
    def __del__(self):        
        moveit_commander.roscpp_shutdown()
        moveit_commander.os._exit(0)
        
    def _open_gripper(self):
        joint_trajectory = JointTrajectory()
        joint_trajectory.header.stamp = rospy.get_rostime()
        joint_trajectory.joint_names = ["m1n6s200_joint_finger_1", "m1n6s200_joint_finger_2"]
        
        joint_trajectory_point = JointTrajectoryPoint()
        joint_trajectory_point.positions = [0, 0]
        joint_trajectory_point.time_from_start = rospy.Duration(5.0)
        
        joint_trajectory.points.append(joint_trajectory_point)
        return joint_trajectory
    
    def _close_gripper(self):
        joint_trajectory = JointTrajectory()
        joint_trajectory.header.stamp = rospy.get_rostime()
        joint_trajectory.joint_names = ["m1n6s200_joint_finger_1", "m1n6s200_joint_finger_2"]
        
        joint_trajectory_point = JointTrajectoryPoint()
        joint_trajectory_point.positions = [1.2, 1.2]
        joint_trajectory_point.time_from_start = rospy.Duration(5.0)
        
        joint_trajectory.points.append(joint_trajectory_point)
        return joint_trajectory

    def make_gripper_translation_approach(self,grasp,size):
        grasp.pre_grasp_approach.direction.header.frame_id = self.end_effector_link
        grasp.pre_grasp_approach.direction.vector.z = size[2]/2
        grasp.pre_grasp_approach.min_distance = 0.0
        grasp.pre_grasp_approach.desired_distance = 0.115

    def make_gripper_translation_retreat(self,grasp,size):
        grasp.post_grasp_retreat.direction.header.frame_id = self.end_effector_link
        grasp.post_grasp_retreat.direction.vector.z = -1 * size[2]/2
        grasp.post_grasp_retreat.min_distance = 0.0
        grasp.post_grasp_retreat.desired_distance = -0.115

    # Template function for creating the Grasps    
    def _create_grasps(self, x, y, z, rotation,size):        
        grasps = []
        #z_gsp_val = [z,1.25*z,1.5*z,1.75*z,2*z]
        print(size)
        z_gsp_val = [z, z+0.25*(size[2]/2),z+0.5*(size[2]/2),z+0.75*(size[2]/2),z+(size[2]/2)]
        # You can create multiple grasps and add them to the grasps list
        for i in range(len(z_gsp_val)):

            grasp = Grasp() # create a new grasp
            
            # Set the pre grasp posture (the fingers)
            ''' Todo '''
            # Set the grasp posture (the fingers)
            ''' Todo '''
            # Set the position of where to grasp
            ''' Todo '''
            # Set the orientation of the end effector 
            ''' Todo '''
            # Set the pre_grasp_approach
            ''' Todo ''' 
            # Set the post_grasp_approach
            ''' Todo '''

            q = quaternion_from_euler(math.pi, 0.0, rotation)
            grasp.grasp_pose.pose.position.x = x
            grasp.grasp_pose.pose.position.y = y
            grasp.grasp_pose.pose.position.z = z_gsp_val[i]
            grasp.grasp_pose.pose.orientation.x = q[0]
            grasp.grasp_pose.pose.orientation.y = q[1]
            grasp.grasp_pose.pose.orientation.z = q[2]
            grasp.grasp_pose.pose.orientation.w = q[3]
             # setting the planning frame (Positive x is to the left, negative Y is to the front of the arm)
            grasp.grasp_pose.header.frame_id = "m1n6s200_link_base"
            grasp.pre_grasp_posture = self._open_gripper()
            grasp.grasp_posture = self._close_gripper()

            grasp.pre_grasp_approach.direction.header.frame_id = self.end_effector_link
            grasp.pre_grasp_approach.direction.vector.z = 1
            grasp.pre_grasp_approach.min_distance = 0.12
            grasp.pre_grasp_approach.desired_distance = 0.15

            grasp.post_grasp_retreat.direction.header.frame_id = self.end_effector_link
            grasp.post_grasp_retreat.direction.vector.z = -1
            grasp.post_grasp_retreat.min_distance = 0.12
            grasp.post_grasp_retreat.desired_distance = 0.15
            
            # grasp.pre_grasp_approach = self.make_gripper_translation_approach(grasp,size)
            # print(grasp.pre_grasp_approach.direction.header.frame_id)
            # grasp.post_grasp_retreat = self.make_gripper_translation_retreat(grasp,size)
            grasps.append(grasp) # add all your grasps in the grasps list, MoveIT will pick the best one    
        return grasps
    
    # Template function, you can add parameters if needed!
    def grasp(self, x, y, z, rotation, size):
        
        # Add collision object, easiest to name the object, "object"
        ''' Todo ''' 
        # Create and return grasps
        ''' Todo ''' 

        self.add_object(x,y,z,rotation,size)
        self.clear_octomap()
        rospy.sleep(1.0)

        grasps = self._create_grasps(x,y,z,rotation,size)
        
	self.close_fingers() # Close the fingers before planning!
	self.move_to(0.35,0,0.25,math.radians(90))
        result = self.arm.pick("object", grasps) # Perform pick on "object", returns result
        if result == MoveItErrorCodes.SUCCESS:
            print 'Success'
	    self.move_to(0.35,0,0.25,math.radians(90))
	    self.move_to_drop_point()
            #self.move_to(0.07762650150394189,0.19728139122386762,0.18509897914268225,92.5137252764)
            self.open_fingers()
	    rospy.sleep(1.0)
	    self.close_fingers()
            rospy.sleep(1.0)
            self.remove_object()
            return True
        else:
            print 'Failed'
            self.move_to(0.35,0,0.25,math.radians(90))
	    self.move_to_drop_point()
            #self.move_to(0.07762650150394189,0.19728139122386762,0.18509897914268225,92.5137252764)
            self.open_fingers()
	    rospy.sleep(1.0)
	    self.close_fingers()
            return False
        
    def open_fingers(self):
        self.gripper.set_joint_value_target([0.0, 0.0])
        self.gripper.go(wait=True)
        rospy.sleep(2.0)
        
    def close_fingers(self):
        self.gripper.set_joint_value_target([1.3, 1.3])
        self.gripper.go(wait=True)
        rospy.sleep(2.0)
    
    def move_to(self, x, y, z, rotation):        
        q = quaternion_from_euler(math.pi, 0.0, rotation)
        pose = PoseStamped()
        pose.header.frame_id = "m1n6s200_link_base"
        pose.pose.position.x = x
        pose.pose.position.y = y
        pose.pose.position.z = z
        pose.pose.orientation.x = q[0]
        pose.pose.orientation.y = q[1]
        pose.pose.orientation.z = q[2]
        pose.pose.orientation.w = q[3]
        
        self.arm.set_pose_target(pose, self.end_effector_link)
        plan = self.arm.plan()
        self.arm.go(wait=True)
        self.arm.stop()
        self.arm.clear_pose_targets()
        
    def print_position(self):        
        pose =  self.arm.get_current_pose()
        self.transformer.waitForTransform("m1n6s200_link_base", "base_footprint", rospy.Time.now(), rospy.Duration(10))
        eef_pose = self.transformer.transformPose("m1n6s200_link_base", pose)
        
        orientation = eef_pose.pose.orientation
        orientation = [orientation.x, orientation.y, orientation.z, orientation.w]
        euler = euler_from_quaternion(orientation)
        print '----------------'
        print orientation
        print "z:", eef_pose.pose.position.x
        print "y:", eef_pose.pose.position.y
        print "z:", eef_pose.pose.position.z
        print "yaw (degrees):", math.degrees(euler[2])
    
    def remove_object(self):
        self.scene.remove_attached_object(self.end_effector_link, "object")
        self.scene.remove_world_object("object")
        
    def add_object(self,x,y,z,rotation,size):
        object_pose = PoseStamped()
        object_pose.header.frame_id = "m1n6s200_link_base"
        object_pose.pose.position.x = x
        object_pose.pose.position.y = y
        object_pose.pose.position.z = z

        q = quaternion_from_euler(math.pi, 0.0, rotation)
        object_pose.pose.orientation.x = q[0]
        object_pose.pose.orientation.y = q[1]
        object_pose.pose.orientation.z = q[2]
        object_pose.pose.orientation.w = q[3]
        self.scene.add_box("object",object_pose, size)
        rospy.sleep(1.0)

    def move_to_drop_point(self):
	
        pose = PoseStamped()
        pose.header.frame_id = "m1n6s200_link_base"
        pose.pose.position.x = 0.2175546259709541
        pose.pose.position.y = 0.18347985269448372
        pose.pose.position.z = 0.16757751444136426

        pose.pose.orientation.x = 0.6934210704552356
        pose.pose.orientation.y =  0.6589390059796749
        pose.pose.orientation.z = -0.23223137602833943
        pose.pose.orientation.w = -0.17616808290725341
        
        self.arm.set_pose_target(pose, self.end_effector_link)
        plan = self.arm.plan()
        self.arm.go(wait=True)
        self.arm.stop()
        self.arm.clear_pose_targets()
         
        
