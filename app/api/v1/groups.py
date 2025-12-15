from typing import Annotated
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, EmailStr
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.response import StandardResponse
from app.core.security import get_current_user
from app.db.models import Group, GroupMember, User
from app.deps import get_db_session


class GroupCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class GroupUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1000)


class GroupResponse(BaseModel):
    id: str
    name: str
    description: str | None = None
    member_count: int = 0
    created_at: str


class InviteMemberRequest(BaseModel):
    user_id: uuid.UUID | None = Field(default=None, description="User ID to invite")
    email: EmailStr | None = Field(default=None, description="Email of user to invite")
    role: str = Field(default="member", pattern="^(owner|admin|member)$")


class MemberResponse(BaseModel):
    id: str
    user_id: str
    username: str
    email: str
    full_name: str | None = None
    role: str
    joined_at: str


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., pattern="^(owner|admin|member)$")


class TransferOwnershipRequest(BaseModel):
    new_owner_id: uuid.UUID | None = Field(default=None, description="User ID of the new owner")
    new_owner_member_id: uuid.UUID | None = Field(default=None, description="Member ID of the new owner")


router = APIRouter(prefix="/groups", tags=["groups"])


async def _get_group_or_404(session: AsyncSession, group_id: uuid.UUID) -> Group:
    """Get group by ID or raise 404."""
    result = await session.execute(select(Group).where(Group.id == group_id))
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    return group


async def _assert_group_permission(
    session: AsyncSession,
    group_id: uuid.UUID,
    user_id: uuid.UUID,
    allowed_roles: tuple[str, ...] = ("owner", "admin"),
) -> GroupMember:
    """Assert user has permission to manage group (owner or admin)."""
    result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user_id,
                GroupMember.role.in_(allowed_roles),
            )
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only group owners and admins can perform this action"
        )
    return member


@router.post("", response_model=StandardResponse[GroupResponse])
async def create_group(
    payload: GroupCreateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[GroupResponse]:
    """Create a new group. The creator becomes the owner."""
    # Check if group name already exists
    result = await session.execute(select(Group).where(Group.name == payload.name))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already exists"
        )
    
    # Create group
    group = Group(
        name=payload.name,
        description=payload.description,
    )
    session.add(group)
    await session.flush()
    
    # Add creator as owner
    owner_member = GroupMember(
        group_id=group.id,
        user_id=current_user.id,
        role="owner",
    )
    session.add(owner_member)
    await session.commit()
    await session.refresh(group)
    
    # Get member count
    member_count_result = await session.execute(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    )
    member_count = member_count_result.scalar() or 0
    
    data = GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        member_count=member_count,
        created_at=group.created_at.isoformat() if group.created_at else "",
    )
    return StandardResponse(data=data)


@router.get("", response_model=StandardResponse[list[GroupResponse]])
async def list_groups(
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[GroupResponse]]:
    """List all groups the current user is a member of."""
    # Get all groups where user is a member
    result = await session.execute(
        select(Group)
        .join(GroupMember, Group.id == GroupMember.group_id)
        .where(GroupMember.user_id == current_user.id)
    )
    groups = result.scalars().unique().all()
    
    data = []
    for group in groups:
        # Get member count
        member_count_result = await session.execute(
            select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
        )
        member_count = member_count_result.scalar() or 0
        
        data.append(GroupResponse(
            id=str(group.id),
            name=group.name,
            description=group.description,
            member_count=member_count,
            created_at=group.created_at.isoformat() if group.created_at else "",
        ))
    
    return StandardResponse(data=data)


@router.get("/{group_id}", response_model=StandardResponse[GroupResponse])
async def get_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[GroupResponse]:
    """Get group details. User must be a member."""
    group = await _get_group_or_404(session, group_id)
    
    # Check if user is a member
    result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Get member count
    member_count_result = await session.execute(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    )
    member_count = member_count_result.scalar() or 0
    
    data = GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        member_count=member_count,
        created_at=group.created_at.isoformat() if group.created_at else "",
    )
    return StandardResponse(data=data)


@router.put("/{group_id}", response_model=StandardResponse[GroupResponse])
async def update_group(
    group_id: uuid.UUID,
    payload: GroupUpdateRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[GroupResponse]:
    """Update group. Only owners and admins can update."""
    group = await _get_group_or_404(session, group_id)
    
    # Check permission
    await _assert_group_permission(session, group_id, current_user.id)
    
    # Update fields
    if payload.name is not None:
        # Check if new name conflicts with existing group
        if payload.name != group.name:
            result = await session.execute(select(Group).where(Group.name == payload.name))
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Group name already exists"
                )
        group.name = payload.name
    
    if payload.description is not None:
        group.description = payload.description
    
    await session.commit()
    await session.refresh(group)
    
    # Get member count
    member_count_result = await session.execute(
        select(func.count(GroupMember.id)).where(GroupMember.group_id == group.id)
    )
    member_count = member_count_result.scalar() or 0
    
    data = GroupResponse(
        id=str(group.id),
        name=group.name,
        description=group.description,
        member_count=member_count,
        created_at=group.created_at.isoformat() if group.created_at else "",
    )
    return StandardResponse(data=data)


@router.delete("/{group_id}", response_model=StandardResponse[dict])
async def delete_group(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """Delete group. Only owners can delete."""
    group = await _get_group_or_404(session, group_id)
    
    # Check if user is owner
    await _assert_group_permission(session, group_id, current_user.id, allowed_roles=("owner",))
    
    # Delete group (cascade will delete members and libraries)
    await session.delete(group)
    await session.commit()
    
    return StandardResponse(data={"deleted": True, "group_id": str(group_id)})


@router.post("/{group_id}/members/invite", response_model=StandardResponse[MemberResponse])
async def invite_member(
    group_id: uuid.UUID,
    payload: InviteMemberRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[MemberResponse]:
    """Invite a user to join the group. Only owners and admins can invite."""
    group = await _get_group_or_404(session, group_id)
    
    # Check permission
    await _assert_group_permission(session, group_id, current_user.id)
    
    # Find user by user_id or email
    user: User | None = None
    if payload.user_id:
        result = await session.execute(select(User).where(User.id == payload.user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    elif payload.email:
        result = await session.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email {payload.email} not found"
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either user_id or email must be provided"
        )
    
    # Check if user is already a member
    existing_result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == user.id,
            )
        )
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this group"
        )
    
    # Add member
    member = GroupMember(
        group_id=group_id,
        user_id=user.id,
        role=payload.role,
    )
    session.add(member)
    await session.commit()
    await session.refresh(member)
    
    data = MemberResponse(
        id=str(member.id),
        user_id=str(user.id),
        username=user.username or "",
        email=user.email,
        full_name=user.full_name,
        role=member.role,
        joined_at=member.created_at.isoformat() if member.created_at else "",
    )
    return StandardResponse(data=data)


@router.get("/{group_id}/members", response_model=StandardResponse[list[MemberResponse]])
async def list_members(
    group_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[list[MemberResponse]]:
    """List all members of a group. User must be a member."""
    group = await _get_group_or_404(session, group_id)
    
    # Check if user is a member
    result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
            )
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this group"
        )
    
    # Get all members
    members_result = await session.execute(
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(GroupMember.group_id == group_id)
        .order_by(GroupMember.role.desc(), GroupMember.created_at.asc())
    )
    
    data = []
    for member, user in members_result.all():
        data.append(MemberResponse(
            id=str(member.id),
            user_id=str(user.id),
            username=user.username or "",
            email=user.email,
            full_name=user.full_name,
            role=member.role,
            joined_at=member.created_at.isoformat() if member.created_at else "",
        ))
    
    return StandardResponse(data=data)


@router.put("/{group_id}/members/{member_id}/role", response_model=StandardResponse[MemberResponse])
async def update_member_role(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    payload: UpdateMemberRoleRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[MemberResponse]:
    """Update a member's role. Only owners and admins can update roles."""
    group = await _get_group_or_404(session, group_id)
    
    # Check permission
    await _assert_group_permission(session, group_id, current_user.id)
    
    # Get member
    result = await session.execute(
        select(GroupMember, User)
        .join(User, GroupMember.user_id == User.id)
        .where(
            and_(
                GroupMember.id == member_id,
                GroupMember.group_id == group_id,
            )
        )
    )
    member_data = result.first()
    if not member_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    
    member, user = member_data
    
    # Prevent changing owner role (only if there's only one owner)
    if member.role == "owner":
        owner_count_result = await session.execute(
            select(func.count(GroupMember.id)).where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.role == "owner",
                )
            )
        )
        owner_count = owner_count_result.scalar() or 0
        if owner_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot change role of the only owner"
            )
    
    # Update role
    member.role = payload.role
    await session.commit()
    await session.refresh(member)
    
    data = MemberResponse(
        id=str(member.id),
        user_id=str(user.id),
        username=user.username or "",
        email=user.email,
        full_name=user.full_name,
        role=member.role,
        joined_at=member.created_at.isoformat() if member.created_at else "",
    )
    return StandardResponse(data=data)


@router.delete("/{group_id}/members/{member_id}", response_model=StandardResponse[dict])
async def remove_member(
    group_id: uuid.UUID,
    member_id: uuid.UUID,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """Remove a member from the group. Only owners and admins can remove members."""
    group = await _get_group_or_404(session, group_id)
    
    # Check permission
    await _assert_group_permission(session, group_id, current_user.id)
    
    # Get member
    result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.id == member_id,
                GroupMember.group_id == group_id,
            )
        )
    )
    member = result.scalar_one_or_none()
    if not member:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    
    # Prevent removing the only owner
    if member.role == "owner":
        owner_count_result = await session.execute(
            select(func.count(GroupMember.id)).where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.role == "owner",
                )
            )
        )
        owner_count = owner_count_result.scalar() or 0
        if owner_count == 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot remove the only owner. Transfer ownership first."
            )
    
    # Remove member
    await session.delete(member)
    await session.commit()
    
    return StandardResponse(data={"removed": True, "member_id": str(member_id)})


@router.post("/{group_id}/transfer-ownership", response_model=StandardResponse[dict])
async def transfer_ownership(
    group_id: uuid.UUID,
    payload: TransferOwnershipRequest,
    session: AsyncSession = Depends(get_db_session),
    current_user: User = Depends(get_current_user),
) -> StandardResponse[dict]:
    """Transfer group ownership to another member. Only current owner can transfer."""
    group = await _get_group_or_404(session, group_id)
    
    # Check if current user is the owner
    current_owner_result = await session.execute(
        select(GroupMember).where(
            and_(
                GroupMember.group_id == group_id,
                GroupMember.user_id == current_user.id,
                GroupMember.role == "owner",
            )
        )
    )
    current_owner = current_owner_result.scalar_one_or_none()
    if not current_owner:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the current owner can transfer ownership"
        )
    
    # Validate that at least one identifier is provided
    if not payload.new_owner_id and not payload.new_owner_member_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either new_owner_id or new_owner_member_id must be provided"
        )
    
    # Find the new owner member
    if payload.new_owner_member_id:
        # Find by member_id
        new_owner_result = await session.execute(
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(
                and_(
                    GroupMember.id == payload.new_owner_member_id,
                    GroupMember.group_id == group_id,
                )
            )
        )
    else:
        # Find by user_id
        new_owner_result = await session.execute(
            select(GroupMember, User)
            .join(User, GroupMember.user_id == User.id)
            .where(
                and_(
                    GroupMember.group_id == group_id,
                    GroupMember.user_id == payload.new_owner_id,
                )
            )
        )
    
    new_owner_data = new_owner_result.first()
    if not new_owner_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="New owner is not a member of this group"
        )
    
    new_owner_member, new_owner_user = new_owner_data
    
    # Prevent transferring to self
    if new_owner_member.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer ownership to yourself"
        )
    
    # Transfer ownership: old owner becomes admin, new owner becomes owner
    current_owner.role = "admin"
    new_owner_member.role = "owner"
    
    await session.commit()
    
    return StandardResponse(data={
        "transferred": True,
        "group_id": str(group_id),
        "new_owner_id": str(new_owner_user.id),
        "new_owner_email": new_owner_user.email,
        "new_owner_username": new_owner_user.username or "",
        "previous_owner_id": str(current_user.id),
    })

