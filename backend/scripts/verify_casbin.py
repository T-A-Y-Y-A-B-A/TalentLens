import casbin
import os

def test_casbin():
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "app", "core"))
    model_path = os.path.join(base_dir, "rbac_model.conf")
    policy_path = os.path.join(base_dir, "rbac_policy.csv")
    enforcer = casbin.Enforcer(model_path, policy_path)
    
    print("Recruiter read jobs:", enforcer.enforce("recruiter", "jobs", "read"))
    print("Recruiter create jobs:", enforcer.enforce("recruiter", "jobs", "create"))
    print("Recruiter update jobs:", enforcer.enforce("recruiter", "jobs", "update"))
    print("Recruiter manage jobs:", enforcer.enforce("recruiter", "jobs", "manage"))
    print("Recruiter delete jobs:", enforcer.enforce("recruiter", "jobs", "delete"))

    print("HR Manager read jobs:", enforcer.enforce("hr_manager", "jobs", "read"))
    print("HR Manager create jobs:", enforcer.enforce("hr_manager", "jobs", "create"))
    print("HR Manager update jobs:", enforcer.enforce("hr_manager", "jobs", "update"))
    print("HR Manager manage jobs:", enforcer.enforce("hr_manager", "jobs", "manage"))
    print("HR Manager delete jobs:", enforcer.enforce("hr_manager", "jobs", "delete"))

    print("Interviewer get candidates:", enforcer.enforce("interviewer", "candidates", "read"))
    print("Interviewer get interviews:", enforcer.enforce("interviewer", "interviews", "read"))
    print("Interviewer manage jobs:", enforcer.enforce("interviewer", "jobs", "manage"))
    
    print("Casbin check complete.")

if __name__ == "__main__":
    test_casbin()
